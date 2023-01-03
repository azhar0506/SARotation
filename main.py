#!/usr/bin/env python

import os
import json 
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
from googleapiclient import discovery
from google.cloud import storage

def listProjects():
    print("Listing Projects... \n")
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

    request = service.projects().list(filter='labels.key_rotate=true')
    response = request.execute()
    print(response)
    return response["projects"]

def removeServiceAccountKeys(service_account):
    print("Removing key from storage...")
    service_account = service_account["name"]
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("service_account_keyts")
    string =  service_account + "/key.json"
    blob = bucket.blob(string)
    if (blob.exists()):
        blob.delete()
    print("Key Removed. \n")
    
def addServiceAccountKeys(service_account, new_key):
    print("Adding key to storage...")
    service_account = service_account["name"]

    storage_client = storage.Client()
    bucket = storage_client.get_bucket("service_account_keyts")
    string = service_account + "/key.json"
    blob = bucket.blob(string)
    
    with blob.open("w") as f:
        f.write(str(json.dumps(new_key)))
    print("Key Added. \n")

def getServiceAccounts(project):
    project_name = project["projectId"]

    print("\nListing Service Accounts from {}... \n".format(project_name))
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials)
    print(project_name+ "... \n")
    sa = service.projects().serviceAccounts().list(name='projects/{0}'.format(project_name)).execute()
    print(sa)
    if ("accounts" in sa):
        return sa["accounts"]
    else:
        return []

def getServiceKeys(service_account):
    service_account = service_account["name"]
    print("\nListing Service Account Keys from {}... \n".format(service_account))
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials)
    keys = service.projects().serviceAccounts().keys().list(name=service_account).execute()
    print(keys)
    if ("keys" in keys):
        return keys["keys"]
    else:
        return []
    
def deleteKey(key_name):
    print("\nDeleting a key...")
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials)
    service.projects().serviceAccounts().keys().delete(name=key_name).execute()
    print("Deleted Key")

def replenishKey(service_account):
    print("\nReplenishing Key...")
    service_account = service_account["name"]
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials)

    key = service.projects().serviceAccounts().keys().create(
        name=service_account, body={}
        ).execute()
    print("Key Replenished")
    return key
    
def rotateStart():
    project_list = listProjects()
    for project in project_list:
        service_accounts = getServiceAccounts(project)
        for sa in service_accounts:
            keys = getServiceKeys(sa)
            keys = filter(lambda key: key["keyType"] != "SYSTEM_MANAGED", keys)
            keys = list(keys)
            for key in keys:
                if (key["keyType"] != "SYSTEM_MANAGED"):
                    deleteKey(key["name"])
                    removeServiceAccountKeys(sa)
                    new_key = replenishKey(sa)
                    addServiceAccountKeys(sa, new_key)
            if (len(keys) <= 0):
                new_key = replenishKey(sa)
                addServiceAccountKeys(sa, new_key)  
            

if __name__ == '__main__':
    rotateStart()
