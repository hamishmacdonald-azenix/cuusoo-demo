# This script will need to be run manually for each deployment to create the KeyVault backed secret scope as 
# this is not currently supported using service principal authentication
# 
# Be sure to export the variables below before running this script:
# TARGET_CONFIG - The name of the config file to use, excluding the file extension

CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"

ARM_TENANT_ID=$(yq eval ".tenantId" ${CONFIG_FILE})
ARM_SUBSCRIPTION_ID=$(yq eval ".subscription_id" ${CONFIG_FILE})

echo ">>> Logging in to Azure CLI."

az login --tenant ${ARM_TENANT_ID}
az account set --subscription ${ARM_SUBSCRIPTION_ID}

# Get the Databricks workspace and KeyVault details
KEYVAULT_SCOPE_NAME=$(yq eval ".keyvault_scope_name" ${CONFIG_FILE})
KEYVAULT_NAME=$(yq eval ".keyvault_name" ${CONFIG_FILE})
KEYVAULT_RESOURCE_ID=$(az keyvault list --query "[?contains(@.name,'${KEYVAULT_NAME}')==\`true\`]".id -o tsv)
KEYVAULT_DNS_NAME="https://${KEYVAULT_NAME}.vault.azure.net/"
DATABRICKS_WORKSPACE_NAME=$(yq eval ".databricks_workspace_name" ${CONFIG_FILE})
DATABRICKS_WORKSPACE_URL=$(az databricks workspace list --query "[?contains(@.name,'${DATABRICKS_WORKSPACE_NAME}')==\`true\`]".workspaceUrl -o tsv)
DATABRICKS_HOST=`echo "https://${DATABRICKS_WORKSPACE_URL}"`

# Get a token for the global Databricks application.
# The resource name is fixed and never changes.
TOKEN_RESPONSE=$(az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d)
DATABRICKS_AUTH_TOKEN=$(jq .accessToken -r <<< "$TOKEN_RESPONSE")
# Get a token for the Azure management API
TOKEN_RESPONSE=$(az account get-access-token --resource https://management.core.windows.net/)
AZ_AUTH_TOKEN=$(jq .accessToken -r <<< "$TOKEN_RESPONSE")

#Get the list of existing scopes
DATABRICKS_SECRET_SCOPES=$(curl -X GET -H "Authorization: Bearer ${DATABRICKS_AUTH_TOKEN}" https://${DATABRICKS_WORKSPACE_URL}/api/2.0/secret/scopes/list)

if [ ${DATABRICKS_SECRET_SCOPES} == "{}" ]
then
    # Build up the json payload
    SCOPE_JSON="$(cat <<EOM
{"scope":"$KEYVAULT_SCOPE_NAME","scope_backend_type":"AZURE_KEYVAULT","backend_azure_keyvault":{"resource_id":"$KEYVAULT_RESOURCE_ID","dns_name":"$KEYVAULT_DNS_NAME"},"initial_manage_principal":"users"}}
EOM
)"
    # Create the scope
    curl --netrc --request POST \
    https://${DATABRICKS_WORKSPACE_URL}/api/2.0/secrets/scopes/create \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${DATABRICKS_AUTH_TOKEN}" \
    --header "X-Databricks-Azure-SP-Management-Token: ${AZ_AUTH_TOKEN}" \
    --data $SCOPE_JSON
fi

