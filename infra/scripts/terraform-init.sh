echo ">>> Importing config file."
CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"

RESOURCE_GROUP_NAME=$(yq eval ".tf_resource_group" ${CONFIG_FILE})
LOCATION=$(yq eval ".tf_location" ${CONFIG_FILE})
STORAGE_ACCOUNT_NAME=$(yq eval ".tf_storage_account" ${CONFIG_FILE})
CONTAINER_NAME=$(yq eval ".tf_container_name" ${CONFIG_FILE})
STATE_FILE=$(yq eval ".tf_statefile" ${CONFIG_FILE})

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
