# This scripts uses MSYS_NO_PATHCONV=1 for all az commands that reference a resource id to prevent POSIX-to-Windows path conversions
# Note that this is only an issue when running Git Bash on Windows
# https://github.com/fengzhou-msft/azure-cli/blob/ea149713de505fa0f8ae6bfa5d998e12fc8ff509/doc/use_cli_with_git_bash.md

export MSYS_NO_PATHCONV=1
CONFIG_FILE="infra/config/${1}.yaml"

ARM_TENANT_ID=$(yq eval ".tenantId" ${CONFIG_FILE})
ARM_CLIENT_ID=$(yq eval ".service_principal_appId" ${CONFIG_FILE})
ARM_SUBSCRIPTION_ID=$(yq eval ".subscription_id" ${CONFIG_FILE})
ARM_CLIENT_SECRET=$2

RG_NAME=$(yq eval ".rg_app_name" ${CONFIG_FILE})
WORKFLOW_NAME=$(yq eval ".logic_app_name" ${CONFIG_FILE})

echo ">>> Logging in to Azure CLI."

az login --service-principal --username ${ARM_CLIENT_ID} --password ${ARM_CLIENT_SECRET} --tenant ${ARM_TENANT_ID}
az account set --subscription ${ARM_SUBSCRIPTION_ID}

echo ">>> Update workflow ${WORKFLOW_NAME}"

# Build up the Key Vault connection ID
KEY_VAULT_CONNECTION_ID="/subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/${RG_NAME}/providers/Microsoft.Web/connections/keyvault"
KEY_VAULT_ID="/subscriptions/${ARM_SUBSCRIPTION_ID}/providers/Microsoft.Web/locations/australiaeast/managedApis/keyvault"

echo "$(cat logic-apps/consumption/workflow.json | jq --arg connection_id ${KEY_VAULT_CONNECTION_ID} --arg id ${KEY_VAULT_ID} '.parameters[].value.keyvault.connectionId |= $connection_id | .parameters[].value.keyvault.id |= $id')" > logic-apps/workflow.json

az logic workflow update --resource-group ${RG_NAME} --name ${WORKFLOW_NAME} --definition logic-apps/workflow.json
rm logic-apps/workflow.json