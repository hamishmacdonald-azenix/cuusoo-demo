import logging
import azure.functions as func
import os
import traceback
import json
from azure.identity import DefaultAzureCredential
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
        storageAccountName = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name="storageAccountGeneric", credential=default_credential)
        storageURL = f"https://{storageAccountName}.blob.core.windows.net"
        container = "config"

        # Get the file config

        config = common.getTaskConfig(config_file_path=taskPath, storage_url=storageURL, container_name=container, credential=default_credential)

        return func.HttpResponse(
                json.dumps(config),
                status_code=200)
                
    except Exception:
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            traceback.format_exc(), status_code=400)