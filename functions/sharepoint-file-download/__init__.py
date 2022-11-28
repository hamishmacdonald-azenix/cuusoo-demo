import logging
import azure.functions as func
import os
import traceback
import yaml
from yaml import Loader
from azure.identity import DefaultAzureCredential
from datetime import datetime
import common

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Get all the parameters from the request body
        req_body = req.get_json()
        taskPath = req_body.get('task_path')

        # Get the MSI credential to access
        default_credential = DefaultAzureCredential()

        # Get all the required config from the app settings
        keyvaultURL = f"https://{os.environ['KEYVAULT_NAME']}.vault.azure.net"
        tempFilePath = os.environ['TEMP_FILE_PATH']
        storageAccountName = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name="storageAccountGeneric", credential=default_credential)
        storageURL = f"https://{storageAccountName}.blob.core.windows.net"
        container = "config"
        configFileName = taskPath.split("/")[-1]
        configFilePath = taskPath.replace(configFileName, "")
        configFile = common.getBlobFile(storage_url=storageURL, container_name=container, blob_name=taskPath, credential=default_credential)
        ymlConfig = yaml.load(configFile, Loader=Loader)

        # Log the start of the job
        jobOutput = f'run_date: {datetime.now()}\r\nrun_status: Running'
        common.writeLog(job_output=jobOutput, config_file_name=configFileName, config_file_path=configFilePath, storage_url=storageURL, container_name=container, credential=default_credential)

        # Get the source config from the YAML file
        tenantID = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("azure_tenant_id"), credential=default_credential)
        clientID = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("client_id"), credential=default_credential)
        clientSecret = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("client_secret"), credential=default_credential)
        # Get the host from Key Vault if it exists
        if "sharepoint_host" in ymlConfig.get("source").get("secrets"):
            sharepointHost = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("sharepoint_host"), credential=default_credential)
        else:
            sharepointHost = ymlConfig.get("source").get("sharepoint_host")
        # Get the site url from Key Vault if it exists
        if "sharepoint_site_url" in ymlConfig.get("source").get("secrets"):
            sharepointSiteURL = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("sharepoint_site_url"), credential=default_credential)
        else:
            sharepointSiteURL = ymlConfig.get("source").get("sharepoint_site_url")
        # Get the folder path from Key Vault if it exists
        if "sharepoint_folder_path" in ymlConfig.get("source").get("secrets"):
            sharepointFolderPath = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("source").get("secrets").get("sharepoint_folder_path"), credential=default_credential)
        else:
            sharepointFolderPath = ymlConfig.get("source").get("sharepoint_folder_path")
        if not sharepointFolderPath:
            sharepointFolderPath = ""
        loadType = ymlConfig.get("source").get("load_type")
        # Get the source config from the YAML file
        targetStorageAccountName = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=ymlConfig.get("target").get("secrets").get("storage_account_name"), credential=default_credential)
        targetStorageContainer = ymlConfig.get("target").get("storage_container_name")
        targetFilePath = ymlConfig.get("target").get("file_path")
        storageURL = f"https://{storageAccountName}.blob.core.windows.net"
        # Check if we need to download all files or just the new files. Use the blob API as the Data Lake API has issues
        targetStorageURL = f"https://{targetStorageAccountName}.blob.core.windows.net"
        targetBlobList = common.getContainerBlobs(name_starts_with=targetFilePath.replace("Unprocessed", "Processed"), container_name=targetStorageContainer, storage_url=targetStorageURL, credential=default_credential)
        targetBlobNameList = [targetBlob.name.split("/")[-1] for targetBlob in targetBlobList]
        sharepointFileList = common.getSharepointFiles(tenant_id=tenantID, client_id=clientID, client_secret=clientSecret, host=sharepointHost, site_url=sharepointSiteURL, folder_path=sharepointFolderPath, temp_File_Path=tempFilePath)
        if targetFilePath[-1] != "/":
            targetFilePath += "/"
        for sharepointFile in sharepointFileList:
            fileExists = False
            if loadType == "new_files":
                if [targetBlobName for targetBlobName in targetBlobNameList if targetBlobName == sharepointFile.name] != []:
                    fileExists = True
            if fileExists == False:
                # Download the file from SharePoint to local storage
                fileName = f"{tempFilePath}{sharepointFile.name}"
                if os.path.exists(fileName):
                    os.remove(fileName)
                sharepointFile.download(to_path=tempFilePath, name=sharepointFile.name)
                fileContent = open(fileName, "r+b").read()
                # Upload the blob to the target storage
                targetBlobPath = targetFilePath + sharepointFile.name
                targetStorageURL = targetStorageURL.replace(".blob.", ".dfs.")
                common.writeLakeBlob(content=fileContent, storage_url=targetStorageURL, file_system=targetStorageContainer, blob_name=targetBlobPath,
                            credential=default_credential)
                # Delete the local file
                if os.path.exists(fileName):
                    os.remove(fileName)

        # Log the completion of the job
        jobOutput = f'run_date: {datetime.now()}\r\nrun_status: Completed'
        common.writeLog(job_output=jobOutput, config_file_name=configFileName, config_file_path=configFilePath, storage_url=storageURL, container_name=container, credential=default_credential)

        return func.HttpResponse(
                f"This HTTP triggered function executed successfully.",
                status_code=200)
                
    except Exception as exc:
        # Log the failure of the job
        job_output = f'run_date: {datetime.now()}\r\nrun_status: Failed\r\nerror_message: "' + str(exc).replace('"', '') + '"'
        common.writeLog(job_output=job_output, config_file_name=configFileName, config_file_path=configFilePath, storage_url=storageURL, container_name=container, credential=default_credential)

        logging.error(traceback.format_exc())
        return func.HttpResponse(
            traceback.format_exc(), status_code=400)