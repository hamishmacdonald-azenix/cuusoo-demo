import logging
import azure.functions as func
import os
import traceback
from azure.identity import DefaultAzureCredential
import common

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Get all the parameters from the request body
        req_body = req.get_json()
        taskPath = req_body.get('task_path')
        runDate = req_body.get('run_date')
        runStatus = req_body.get('run_status')
        errorMessage = req_body.get('error_message')

        # Get the MSI credential to access
        default_credential = DefaultAzureCredential()

        # Get all the required config from the app settings
        keyvaultURL = f"https://{os.environ['KEYVAULT_NAME']}.vault.azure.net"
        storageAccountName = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name="storageAccountGeneric", credential=default_credential)
        storageURL = f"https://{storageAccountName}.blob.core.windows.net"
        container = "config"
        configFileName = taskPath.split("/")[-1]
        configFilePath = taskPath.replace(configFileName, "")

        # Log the start of the job
        if errorMessage is not None:
            errorMessage = errorMessage.replace('"', "'")
            jobOutput = f'run_date: {runDate}\r\nrun_status: {runStatus}\r\nerror_message: "{errorMessage}"'
        else:
            jobOutput = f'run_date: {runDate}\r\nrun_status: {runStatus}'

        common.writeLog(job_output=jobOutput, config_file_name=configFileName, config_file_path=configFilePath, storage_url=storageURL, container_name=container, credential=default_credential)

        return func.HttpResponse(
                f"This HTTP triggered function executed successfully.",
                status_code=200)
                
    except Exception:
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            traceback.format_exc(), status_code=400)