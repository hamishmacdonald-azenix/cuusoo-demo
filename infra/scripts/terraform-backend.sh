echo ">>> Importing config file."
CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"

RESOURCE_GROUP_NAME=$(yq eval ".tf_resource_group" ${CONFIG_FILE})
LOCATION=$(yq eval ".tf_location" ${CONFIG_FILE})
STORAGE_ACCOUNT_NAME=$(yq eval ".tf_storage_account" ${CONFIG_FILE})
CONTAINER_NAME=$(yq eval ".tf_container_name" ${CONFIG_FILE})
STATE_FILE=$(yq eval ".tf_statefile" ${CONFIG_FILE})

echo ">>> Creating Storage Account for Terraform Backend."

# Create resource group
az group create \
  --name ${RESOURCE_GROUP_NAME} \
  --location ${LOCATION}

# Create storage account
az storage account create \
  --resource-group ${RESOURCE_GROUP_NAME}  \
  --name ${STORAGE_ACCOUNT_NAME} \
  --sku Standard_LRS \
  --encryption-services blob

# Set account to enable soft delete
az storage account blob-service-properties update \
  --enable-container-delete-retention true \
  --container-delete-retention-days 7 \
  --account-name ${STORAGE_ACCOUNT_NAME} \
  --resource-group ${RESOURCE_GROUP_NAME}

# Get Account Key to Generate SAS Token
ACCOUNT_KEY=$(az storage account keys list --resource-group ${RESOURCE_GROUP_NAME} --account-name ${STORAGE_ACCOUNT_NAME} --query '[0].value' -o tsv)

# Create blob container
az storage container create \
  --name ${CONTAINER_NAME} \
  --account-name ${STORAGE_ACCOUNT_NAME} \
  --account-key ${ACCOUNT_KEY}

echo ">>> Initialising Terraform Backend."

cd ../terraform
terraform init \
  -input=false \
  -reconfigure \
  -backend-config="resource_group_name=${RESOURCE_GROUP_NAME}" \
  -backend-config="storage_account_name=${STORAGE_ACCOUNT_NAME}" \
  -backend-config="container_name=${CONTAINER_NAME}" \
  -backend-config="key=${STATE_FILE}" \
  -backend-config="access_key=${ACCOUNT_KEY}"
