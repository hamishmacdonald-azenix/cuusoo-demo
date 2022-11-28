CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"

TENANT_ID=$(yq eval ".tenantId" ${CONFIG_FILE})
CLIENT_ID=$(yq eval ".service_principal_appId" ${CONFIG_FILE})
SUBSCRIPTION_ID=$(yq eval ".subscription_id" ${CONFIG_FILE})

echo ">>> Logging in to Azure CLI."

az login --service-principal --username ${CLIENT_ID} --password ${ARM_CLIENT_SECRET} --tenant ${TENANT_ID}
az account set --subscription ${SUBSCRIPTION_ID}

# Get the Databricks workspace and KeyVault details
KEYVAULT_NAME=$(yq eval ".keyvault_name" ${CONFIG_FILE})
KEYVAULT_RESOURCE_ID=$(az keyvault list --query "[?contains(@.name,'${KEYVAULT_NAME}')==\`true\`]".id -o tsv)
KEYVAULT_SECRET_NAME="databricksPATToken"
DATABRICKS_WORKSPACE_NAME=$(yq eval ".databricks_workspace_name" ${CONFIG_FILE})
DATABRICKS_LOCATION=$(az databricks workspace list --query "[?contains(@.name,'${DATABRICKS_WORKSPACE_NAME}')==\`true\`]".location -o tsv)
if [ ! -z "$KEYVAULT_RESOURCE_ID" ]
then
    DATABRICKS_PAT_TOKEN_SECRET=$(az keyvault secret list --vault-name ${KEYVAULT_NAME} --query "[?contains(@.name,'${KEYVAULT_SECRET_NAME}')==\`true\`]".name -o tsv)
fi
DATABRICKS_RESOURCE_ID=$(az databricks workspace list --query "[?contains(@.name,'${DATABRICKS_WORKSPACE_NAME}')==\`true\`]".id -o tsv)

# Generate a PAT token if it doesn't already exist
if [ ! -z "$DATABRICKS_RESOURCE_ID" ] && [ ! -z "$KEYVAULT_RESOURCE_ID" ] && [ -z "$DATABRICKS_PAT_TOKEN_SECRET" ]
then 

    # Get a token for the global Databricks application.
    # The resource name is fixed and never changes.
    TOKEN_RESPONSE=$(az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d)
    DATABRICKS_AUTH_TOKEN=$(jq .accessToken -r <<< "$TOKEN_RESPONSE")

    # Get a token for the Azure management API
    TOKEN_RESPONSE=$(az account get-access-token --resource https://management.core.windows.net/)
    AZ_AUTH_TOKEN=$(jq .accessToken -r <<< "$TOKEN_RESPONSE")

    # Generate the PAT token
    api_response=$(curl -sf https://$DATABRICKS_LOCATION.azuredatabricks.net/api/2.0/token/create \
    -H "Authorization: Bearer $DATABRICKS_AUTH_TOKEN" \
    -H "X-Databricks-Azure-SP-Management-Token:$AZ_AUTH_TOKEN" \
    -H "X-Databricks-Azure-Workspace-Resource-Id:$DATABRICKS_RESOURCE_ID" \
    -d '{ "comment": "Auto generated for automation" }')
    DATABRICKS_PAT_TOKEN=$(jq .token_value -r <<< "$api_response")

    # Add to KeyVault
    az keyvault secret set --vault-name ${KEYVAULT_NAME} --name $KEYVAULT_SECRET_NAME --value $DATABRICKS_PAT_TOKEN
fi