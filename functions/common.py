import yaml
import requests
import json
from requests.auth import HTTPBasicAuth
from yaml import Loader
from azure.storage.blob import BlobClient, ContainerClient
from azure.storage.filedatalake import DataLakeFileClient, DataLakeServiceClient
from azure.keyvault.secrets import SecretClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import RunFilterParameters, RunQueryFilter, RunQueryOrderBy
from O365 import Account, FileSystemTokenBackend
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from databricks_cli.sdk import ApiClient, ClusterService
from databricks_cli.dbfs.api import *
import zipfile_deflate64 as ZipFile
import traceback
import concurrent.futures
import itertools

def writeBlob(content, storage_url, container_name, blob_name, credential):
    """
    Write an Azure storage blob
    """
    file = BlobClient(account_url=storage_url, container_name=container_name,
                              blob_name=blob_name, credential=credential)
    file.upload_blob(content, overwrite=True)

def writeLakeBlob(content, storage_url, file_system, blob_name, credential):
    """
    Write an Azure data lake blob
    """
    file = DataLakeFileClient(account_url=storage_url, file_system_name=file_system,
                              file_path=blob_name, credential=credential)
    file.create_file()
    file.append_data(content, offset=0, length=len(content))
    file.flush_data(len(content))

def getBlobFile(storage_url, container_name, blob_name, credential):
    """
    Retrieve a blob from an Azure storage account
    """
    file = BlobClient(account_url=storage_url, container_name=container_name,
                      blob_name=blob_name, credential=credential)
    stream = file.download_blob()
    fileStream = stream.readall()
    return fileStream

def getContainerBlobs(storage_url, container_name, credential, name_starts_with = None):
    """
    Retrieve all the blobs from an Azure storage account container
    """
    container = ContainerClient(account_url=storage_url, container_name=container_name,
                                credential=credential)
    if name_starts_with:
        return container.list_blobs(name_starts_with=name_starts_with)
    else:
        return container.list_blobs()

def getDirectoryBlobs(storage_url, file_system_name, directory_name, credential):
    """
    Retrieve all the blobs from an Azure data lake storage account container
    """
    serviceClient = DataLakeServiceClient(account_url=storage_url, credential=credential)
    fileSystemClient = serviceClient.get_file_system_client(file_system=file_system_name)
    try: 
        directory = fileSystemClient.get_paths(path=directory_name)
    except:
        print("Directory does not exist")
    
    return directory

def getKeyvaultSecret(vault_url, secret_name, credential):
    """
    Fetch an Azure Key Vault secret
    """
    vault = SecretClient(vault_url=vault_url, credential=credential)
    secret = vault.get_secret(secret_name)
    return secret.value

def getSharepointFiles(tenant_id, client_id, client_secret, host, site_url, folder_path, temp_File_Path):
    """
    Retrieve a list of all files from a SharePoint site
    """
    credentials = (client_id, client_secret)
    # Authenticate to SharePoint using an Azure AD service principal
    # Use a new token backend to store the token in a writeable directory
    token_backend = FileSystemTokenBackend(token_path=f"{temp_File_Path}token", token_filename='O365.txt')
    account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id, token_backend=token_backend)
    account.authenticate()
    site = account.sharepoint().get_site(host, site_url)
    # Filter down to the specified folder if one is specified
    if folder_path != "":
        files = site.site_storage.get_default_drive().get_item_by_path(folder_path).get_items()
    else:
        files = site.site_storage.get_default_drive().get_root_folder().get_items()
    return files

def writeLog(job_output, config_file_path, config_file_name, storage_url, container_name, credential):
    """
    Write progress to a log file
    """
    logDate = str(datetime.now().date())
    logBlobPath = config_file_path + "Log/" + logDate + "/" + config_file_name.split(".")[0] + ".log"
    writeBlob(content=job_output, storage_url=storage_url, container_name=container_name, blob_name=logBlobPath, credential=credential)

def getLogStatus(config_file_path, config_file_name, storage_url, container_name, credential, log_list = None):
    """
    Retrieve the status of the last run from the log file. Optionally, pass in a list of log files to iterate through
    """
    latestLogFileName = ""
    latestRunDate = ""
    logPath = config_file_path + "Log/"
    
    if log_list:
        blobList = [blob for blob in log_list]
    else:
        blobs = getContainerBlobs(storage_url=storage_url, container_name=container_name, credential = credential, name_starts_with=logPath)
        blobList = [{"name": blob.name, "creation_time": blob.creation_time} for blob in blobs]
    # Get the latest log file for the given config
    if len(blobList) > 0:
        latestBlobList = [str(blob["creation_time"]) for blob in blobList if logPath in blob["name"] and config_file_name.split(".")[0] in blob["name"].split("/")[-1].split(".")[0]]
        if len(latestBlobList) > 0:
            latestRunDate = max(latestBlobList)
            if latestRunDate != "" and latestRunDate is not None:
                latestLogFileName = max([blob["name"] for blob in blobList if logPath in blob["name"] and config_file_name.split(".")[0] in blob["name"].split("/")[-1].split(".")[0] and str(blob["creation_time"]) == latestRunDate])
    # Read the file to get the latest run date and status 
    if latestLogFileName != "":
        configOutput = getBlobFile(storage_url=storage_url, container_name=container_name, blob_name=latestLogFileName, credential=credential)
        ymlConfig = yaml.load(configOutput, Loader=Loader)
        return ymlConfig["run_status"], ymlConfig["run_date"]
    else:
        return "None", ""

def getSystemConfig(storage_url, container_name, credential):
    """
    Retrieve the master system config
    """
    blobPath = "master.yml"
    configFile = getBlobFile(storage_url=storage_url, container_name=container_name, blob_name=blobPath, credential=credential)
    ymlConfig = yaml.load(configFile, Loader=Loader)
    return ymlConfig["systems"]

def getTaskConfig(config_file_path, storage_url, container_name, credential):
    """
    Retrieve the task config for a given task
    """
    configFile = getBlobFile(storage_url=storage_url, container_name=container_name, blob_name=config_file_path, credential=credential)
    ymlConfig = yaml.load(configFile, Loader=Loader)
    return ymlConfig

def getPipelineLatestRunStatus(subscription_id, resource_group_name, data_factory_name, pipeline_name, system_name, credential):
    """
    Retrieve the lastest Data Factory pipeline run status
    """
    dataFactoryClient = DataFactoryManagementClient(credential=credential, subscription_id=subscription_id)
    pipelineFilter = RunQueryFilter(operand="PipelineName", operator="Equals", values=[pipeline_name])
    filterOrderBy = RunQueryOrderBy(order_by="RunStart", order="DESC")
    filterParameters = RunFilterParameters(last_updated_before=datetime(9999, 1, 1, tzinfo=timezone.utc), last_updated_after=datetime(1970, 1, 1, tzinfo=timezone.utc), filters=[pipelineFilter], order_by=[filterOrderBy])
    response = dataFactoryClient.pipeline_runs.query_by_factory(resource_group_name=resource_group_name,factory_name=data_factory_name,filter_parameters=filterParameters)
    # We only need to check the latest execution status
    pipelineStatus = "Never Run"
    for pipelineRun in response.value:
        try:
            if pipelineRun.parameters["system_name"] == system_name:
                pipelineStatus = pipelineRun.status 
                break
        except:
            print("Pipeline not executed with a system_name parameter")
    return pipelineStatus

def newPipelineRun(subscription_id, resource_group_name, data_factory_name, pipeline_name, parameters, credential):
    """
    Create a new Data Factory pipeline run
    """
    dataFactoryClient = DataFactoryManagementClient(credential=credential, subscription_id=subscription_id)
    pipelineRun = dataFactoryClient.pipelines.create_run(resource_group_name=resource_group_name, factory_name=data_factory_name, pipeline_name=pipeline_name, parameters=parameters)
    return pipelineRun.run_id

def getImmutaArchiveDatabricksFile(fileName, keyvaultURL, credential, immutaVersionNo="latest", databricksVersionNo="9"):
    """
    Download a Databricks file from the Immuta Archive store
    """
    immutaDatabrickArchiveURL = "https://archives.immuta.com/hadoop/databricks/"
    immutaArchiveUsername = getKeyvaultSecret(vault_url=keyvaultURL, secret_name="immutaArchiveUsername", credential=credential)
    immutaArchivePassword = getKeyvaultSecret(vault_url=keyvaultURL, secret_name="immutaArchivePassword", credential=credential)
    immutaVersionPath = ""
    # Loop to the latest version if need be
    if immutaVersionNo == "latest":
        response = requests.get(url=immutaDatabrickArchiveURL, auth=HTTPBasicAuth(immutaArchiveUsername, immutaArchivePassword))
        immutaVersions = BeautifulSoup(str(response.content), "html")
        # Get the latest Immuta Version
        for version in immutaVersions.find_all("a", href=True):
            if str(version) > str(immutaVersionPath):
                immutaVersionPath = version["href"]
    else:
        immutaVersionPath = immutaVersionNo + "/"
    # Check the Spark version
    if immutaVersionPath != "":
        databricksVersionPath = ""
        immutaDatabrickArchiveURL += immutaVersionPath
        response = requests.get(url=immutaDatabrickArchiveURL, auth=HTTPBasicAuth(immutaArchiveUsername, immutaArchivePassword)).content
        databricksVersions = BeautifulSoup(response, "html")
        for databricksVersion in databricksVersions.find_all("a", href=True):
            if databricksVersionNo in databricksVersion["href"]:
                databricksVersionPath = databricksVersion["href"]
                break
    # Get the file content
    if databricksVersionPath != "":
        immutaDatabrickArchiveURL += databricksVersionPath + fileName
        response = requests.get(url=immutaDatabrickArchiveURL, auth=HTTPBasicAuth(immutaArchiveUsername, immutaArchivePassword)).content
    else:
        response = ""
    return response

def uploadDatabricksDBFSFiles(databricks_url, databricks_token, file_path, dbfs_file_path, overwrite=True, recursive=False):
    """
    Upload a file to the Databricks DBFS
    """
    dbClient = ApiClient(host=databricks_url, token=databricks_token)
    dbfsApi = DbfsApi(dbClient)
    dbfsApi.cp(src=file_path, dst=dbfs_file_path, overwrite=overwrite, recursive=recursive)
    
    return 

def getDatabricksClusters(databricks_url: str, databricks_token: str) -> str:
    """
    Get a list of the clusters in a given Databricks workspace
    """
    dbClient = ApiClient(host=databricks_url, token=databricks_token)
    clusterService = ClusterService(dbClient)
    clusterList = clusterService.list_clusters()["clusters"]
    clusterList = [{"cluster_id": cluster["cluster_id"], "cluster_name": cluster["cluster_name"]} for cluster in clusterList]
    
    return clusterList

def getBoxToken(client_id, client_secret, box_subject_type, box_subject_id):
    """
    Get a token from the Box API
    """
    tokenURL = "https://api.box.com/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        "client_id":  f"{client_id}",
        "client_secret": f"{client_secret}",
        "grant_type": "client_credentials",
        "box_subject_type": f"{box_subject_type}",
        "box_subject_id": f"{box_subject_id}"
    }
    token = json.loads(requests.post(url=tokenURL, headers=headers, data=body).content)["access_token"]
    
    return token

def getBoxFolderFiles(token, folderID, sortByAttribute="id", sortOrder="asc"):
    """
    Get the list of files from a Box folder
    """

    fileList = []

    def getFileAttribute(file):
        return file[sortByAttribute]

    filesURL = f"https://api.box.com/2.0/folders/{folderID}/items?limit=1000"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    files = json.loads((requests.get(url=filesURL, headers=headers)).content)

    if "entries" in files:
        reverse = False
        if sortOrder.upper() == "DESC":
            reverse = True
        fileList = [file for file in files["entries"] if file["type"] == "file"]
        # Sort the list by the specified attribute and sort order
        fileList.sort(reverse=reverse, key=getFileAttribute)

    return fileList

def getBoxFolderItems(token, folder_id):
    """
    Get the list of all items in a Box folder
    """

    filesURL = f"https://api.box.com/2.0/folders/{folder_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    items = json.loads((requests.get(url=filesURL, headers=headers)).content).get("item_collection").get("entries")
    
    return items

def getBoxFolders(token: str, search_term: str, folder_name: str):
    """
    Get the list of folder in Box based on a search term
    """

    search_url = f"https://api.box.com/2.0/search?query={search_term}&type=folder&limit=10000"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if "entries" in json.loads((requests.get(url=search_url, headers=headers)).content):
        folder_list = [folder.get("id") for folder in json.loads((requests.get(url=search_url, headers=headers)).content).get("entries") if folder_name in folder.get("name")]
    else:
        folder_list = []
    
    return folder_list

def downloadBoxFile(token, fileID, filePath, unzip=False, renameToZipFilename=False, appendZipFilenameToFilename=False, unzipFileType="zip"):
    """
    Download a Box file. Unzip it if required and return a list of the downloaded or extracted files
    """

    downloadURL = f"https://api.box.com/2.0/files/{fileID}/content"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    fileContent = requests.get(url=downloadURL, headers=headers).content
    # Write the Box file content to disk
    try:
        with open(filePath, mode="w+b") as file:
            fileName = os.path.basename(file.name)
            file.write(fileContent)
            file.close()
    except:
        print(f"Error writing file {filePath} to disk: {traceback.format_exc()}")
    fileList = []
    # Unzip the file if required. Rename the extracted file to the name of the zip file if require
    if unzip:
        try:    
            zipExtractPath = filePath.split(".")[0] + "/"
            zipFile = ZipFile.ZipFile(filePath, mode = "r")
            zipFile.extractall(path=zipExtractPath)
            zipFile.close()
            os.remove(filePath)
        except Exception:
            print(f"Unable to extract zip file {filePath}: {traceback.format_exc()}")
        for file in os.listdir(zipExtractPath):
            fileExtension = file.split(".")[-1]
            if fileExtension.lower() == unzipFileType.lower() or unzipFileType == "":
                if renameToZipFilename or appendZipFilenameToFilename:
                    fileNameNew = fileName.split(".")[0] + "." + fileExtension
                    if appendZipFilenameToFilename:
                        fileNameNew = fileName.split(".")[0] + "_" + file.replace("." + fileExtension, "") + "." + fileExtension
                    targetFileName = zipExtractPath + fileNameNew
                    if os.path.exists(targetFileName):
                        os.remove(targetFileName)
                    os.rename(zipExtractPath + file, targetFileName)
                else:
                    targetFileName = zipExtractPath + file
                # Rename the file if the length is over 256 characters
                if len(targetFileName) >= 256:
                    renamedTargetFileName = targetFileName[0:255 - len(fileExtension)] + "." + fileExtension
                    if os.path.exists(renamedTargetFileName):
                        os.remove(renamedTargetFileName)
                    os.rename(targetFileName, renamedTargetFileName)
                else:
                    renamedTargetFileName = targetFileName
                # Append the file to the list of files
                fileList.append(renamedTargetFileName) 
    else:
        # Append the file to the list of files
        fileList.append(filePath)
    
    return fileList

def parallel_run(mapper, items, apply_flat_map=False):
    """
    Invoke the parallel execution of a function
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(mapper, items)
        results = list(results)
        if apply_flat_map:
            results = list(itertools.chain(*results)) # flat map
        return results