CONFIG_FILE=$1
ARM_CLIENT_SECRET=$2
ARM_TENANT_ID=$(jq -r ".azure.tenant_Id" ${CONFIG_FILE})
ARM_SUBSCRIPTION_ID=$(jq -r ".azure.subscription_id" ${CONFIG_FILE})
ARM_CLIENT_ID=$(jq -r ".azure.service_principal_appId" ${CONFIG_FILE})

echo ">>> Logging in to Azure CLI."

az login --service-principal --user ${ARM_CLIENT_ID} --password ${ARM_CLIENT_SECRET} --tenant ${ARM_TENANT_ID}
az account set --subscription ${ARM_SUBSCRIPTION_ID}

# Get the Databricks PAT and workspace URL from Key Vault
KEYVAULT_NAME=$(jq -r '.azure.keyvault_name' ${CONFIG_FILE})
KEYVAULT_SECRET_NAME="databricksPATServiceAccount"
export DATABRICKS_TOKEN=$(az keyvault secret show --vault-name ${KEYVAULT_NAME} --name ${KEYVAULT_SECRET_NAME} --query "value" -o tsv)
export DATABRICKS_HOST="https://"$(az keyvault secret show --vault-name ${KEYVAULT_NAME} --name databricksBaseURL --query "value" -o tsv)