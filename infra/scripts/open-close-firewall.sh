# This scripts uses MSYS_NO_PATHCONV=1 for all az commands that reference a resource id to prevent POSIX-to-Windows path conversions
# Note that this is only an issue when running Git Bash on Windows
# https://github.com/fengzhou-msft/azure-cli/blob/ea149713de505fa0f8ae6bfa5d998e12fc8ff509/doc/use_cli_with_git_bash.md

OPERATION=$1
RULE_TYPE=$2
CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"

TENANT_ID=$(yq eval ".tenantId" ${CONFIG_FILE})
CLIENT_ID=$(yq eval ".service_principal_appId" ${CONFIG_FILE})
SUBSCRIPTION_ID=$(yq eval ".subscription_id" ${CONFIG_FILE})

echo ">>> Logging in to Azure CLI."

az login --service-principal --username ${CLIENT_ID} --password ${ARM_CLIENT_SECRET} --tenant ${TENANT_ID}
az account set --subscription ${SUBSCRIPTION_ID}

# Get the details for the key vault and data lake resources
KEYVAULT_NAME=$(yq eval ".keyvault_name" ${CONFIG_FILE})
KEYVAULT_RESOURCE_GROUP=$(az keyvault list --query "[?contains(@.name,'${KEYVAULT_NAME}')==\`true\`]".resourceGroup -o tsv)
DATALAKE_NAME=$(yq eval ".storage_account_name_datalake" ${CONFIG_FILE})
DATALAKE_RESOURCE_GROUP=$(az storage account list --query "[?contains(@.name,'${DATALAKE_NAME}')==\`true\`]".resourceGroup -o tsv)
# Get the current IP address to add to / remove from the firewalls
if [ ${RULE_TYPE} == "ip" ]
then
    IP_ADDRESS=$(curl ifconfig.me)
fi
# Get the subnet details if required
if [ ${RULE_TYPE} == "subnet" ]
then
    OCTOPUS_VNET_NAME=$(az network vnet list --resource-group octopusRG --query "[?contains(@.name,'-oct-')==\`true\`]".name -o tsv)
    OCTOPUS_SUBNET_ID=$(az network vnet subnet list --resource-group octopusRG --vnet-name ${OCTOPUS_VNET_NAME} --query "[?contains(@.name,'-oct-')==\`true\`]".id -o tsv)
fi

# Add firewall rules to open the services
if [ ${OPERATION} == "open" ] && [ ${RULE_TYPE} == "ip" ]
then
    # Storage
    az storage account network-rule add --resource-group ${DATALAKE_RESOURCE_GROUP} --account-name ${DATALAKE_NAME} --ip-address ${IP_ADDRESS}
    # Key Vault
    az keyvault network-rule add --name ${KEYVAULT_NAME} --resource-group ${KEYVAULT_RESOURCE_GROUP} --ip-address "${IP_ADDRESS}/32"
    az keyvault network-rule wait --name ${KEYVAULT_NAME} --updated
elif [ ${OPERATION} == "open" ] && [ ${RULE_TYPE} == "subnet" ]
then
    # Storage
    MSYS_NO_PATHCONV=1 az storage account network-rule add --resource-group ${DATALAKE_RESOURCE_GROUP} --account-name ${DATALAKE_NAME} --subnet ${OCTOPUS_SUBNET_ID}
    # Key Vault
    MSYS_NO_PATHCONV=1 az keyvault network-rule add --name ${KEYVAULT_NAME} --resource-group ${KEYVAULT_RESOURCE_GROUP} --subnet ${OCTOPUS_SUBNET_ID}
    az keyvault network-rule wait --name ${KEYVAULT_NAME} --updated
# Remove firewall rules
elif [ ${OPERATION} == "close" ] && [ ${RULE_TYPE} == "ip" ]
then
    # Storage
    az storage account network-rule remove --resource-group ${DATALAKE_RESOURCE_GROUP} --account-name ${DATALAKE_NAME} --ip-address ${IP_ADDRESS}
    # Key Vault
    az keyvault network-rule remove --name ${KEYVAULT_NAME} --resource-group ${KEYVAULT_RESOURCE_GROUP} --ip-address "${IP_ADDRESS}/32"
    az keyvault network-rule wait --name ${KEYVAULT_NAME} --updated
elif [ ${OPERATION} == "close" ] && [ ${RULE_TYPE} == "subnet" ]
then
    # Storage
    MSYS_NO_PATHCONV=1 az storage account network-rule remove --resource-group ${DATALAKE_RESOURCE_GROUP} --account-name ${DATALAKE_NAME} --subnet ${OCTOPUS_SUBNET_ID}
    # Key Vault
    MSYS_NO_PATHCONV=1 az keyvault network-rule remove --name ${KEYVAULT_NAME} --resource-group ${KEYVAULT_RESOURCE_GROUP} --subnet ${OCTOPUS_SUBNET_ID}
    az keyvault network-rule wait --name ${KEYVAULT_NAME} --updated
fi