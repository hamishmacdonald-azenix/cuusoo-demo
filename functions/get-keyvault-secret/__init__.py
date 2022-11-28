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
        secretName = req_body.get('secret_name')

        # Get the MSI credential to access
        default_credential = DefaultAzureCredential()

        # Get all the required config from the app settings
        keyvaultURL = f"https://{os.environ['KEYVAULT_NAME']}.vault.azure.net"
        secretValue = common.getKeyvaultSecret(vault_url=keyvaultURL, secret_name=secretName, credential=default_credential)

        return func.HttpResponse(
                json.dumps({"secret_value": secretValue}),
                status_code=200)
                
    except Exception:
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            traceback.format_exc(), status_code=400)