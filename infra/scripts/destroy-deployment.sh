CONFIG_FILE="../config/${TARGET_CONFIG}.yaml"
echo ">>> Destroying resource groups and purging keyvault instance"

# Delete all the RG's if they exist
# Delete all of the diagnostics settings for all resources to prevent orphaned resources from preventing re-deployment

# Data

RG_NAME=$(yq eval ".rg_data_name" ${CONFIG_FILE})
RG_EXISTS=$(az group exists --name ${RG_NAME})

if $RG_EXISTS
then 
    RESOURCES=$(az resource list --resource-group ${RG_NAME} --query "[].{Name:name,Type:type}")
    for RESOURCE in $(echo "${RESOURCES}" | jq -c -r '.[]')
    do
        RESOURCE_NAME=$(echo "${RESOURCE}" | jq -c -r '.Name')
        RESOURCE_TYPE=$(echo "${RESOURCE}" | jq -c -r '.Type')
        DIAGNOSTIC_SETTING=$(az monitor diagnostic-settings list --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE} | jq -c -r '.[]')
        if [ "${DIAGNOSTIC_SETTING}" != "[]" ]
        then
            echo "Deleting diagnostics setting for resource ${RESOURCE_NAME} in resource group ${RG_NAME}"
            az monitor diagnostic-settings delete --name default --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE}
        fi
    done

    #Remove the ADF managed private endpoints to prevent orohaned resources from preventing a re-deployment
    DATA_FACTORY_NAME=$(yq eval ".data_factory_name" ${CONFIG_FILE})
    DATA_FACTORY_RESOURCE_ID=$(az datafactory list --query "[?contains(@.name,'${DATA_FACTORY_NAME}')==\`true\`]".id -o tsv)

    if [ ! -z "$DATA_FACTORY_RESOURCE_ID" ]
    then
        MPE_LIST=$(az datafactory managed-private-endpoint list --resource-group ${RG_NAME} --factory-name ${DATA_FACTORY_NAME} --managed-virtual-network-name "default" --query "[].{Name:name}")
        for MPE in $(echo "${MPE_LIST}" | jq -c -r '.[].Name' | sed -z 's/\r//g')
        do
            echo "Deleting managed private endpoint ${MPE} for data factory ${DATA_FACTORY_NAME}"
            az datafactory managed-private-endpoint delete --factory-name ${DATA_FACTORY_NAME} --name ${MPE} --managed-virtual-network-name "default" --resource-group ${RG_NAME} --yes
        done
    fi

    echo "Removing resource group ${RG_NAME}"
    az group delete --name ${RG_NAME} --yes
fi

# Security

RG_NAME=$(yq eval ".rg_security_name" ${CONFIG_FILE})
RG_EXISTS=$(az group exists --name ${RG_NAME})

if $RG_EXISTS
then 
    RESOURCES=$(az resource list --resource-group ${RG_NAME} --query "[].{Name:name,Type:type}")
    for RESOURCE in $(echo "${RESOURCES}" | jq -c -r '.[]')
    do
        RESOURCE_NAME=$(echo "${RESOURCE}" | jq -c -r '.Name')
        RESOURCE_TYPE=$(echo "${RESOURCE}" | jq -c -r '.Type')
        DIAGNOSTIC_SETTING=$(az monitor diagnostic-settings list --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE} | jq -c -r '.[]')
        if [ "${DIAGNOSTIC_SETTING}" != "[]" ]
        then
            echo "Deleting diagnostics setting for resource ${RESOURCE_NAME} in resource group ${RG_NAME}"
            az monitor diagnostic-settings delete --name default --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE}
        fi
    done

    echo "Removing resource group ${RG_NAME}"
    az group delete --name ${RG_NAME} --yes
fi

# Admin

RG_NAME=$(yq eval ".rg_admin_name" ${CONFIG_FILE})
RG_EXISTS=$(az group exists --name ${RG_NAME})

if $RG_EXISTS
then 
    echo "Removing resource group ${RG_NAME}"
    az group delete --name ${RG_NAME} --yes
fi

# App

RG_NAME=$(yq eval ".rg_app_name" ${CONFIG_FILE})
RG_EXISTS=$(az group exists --name ${RG_NAME})

if $RG_EXISTS
then 
    RESOURCES=$(az resource list --resource-group ${RG_NAME} --query "[].{Name:name,Type:type}")
    for RESOURCE in $(echo "${RESOURCES}" | jq -c -r '.[]')
    do
        RESOURCE_NAME=$(echo "${RESOURCE}" | jq -c -r '.Name')
        RESOURCE_TYPE=$(echo "${RESOURCE}" | jq -c -r '.Type')
        DIAGNOSTIC_SETTING=$(az monitor diagnostic-settings list --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE} | jq -c -r '.[]')
        if [ "${DIAGNOSTIC_SETTING}" != "[]" ]
        then
            echo "Deleting diagnostics setting for resource ${RESOURCE_NAME} in resource group ${RG_NAME}"
            az monitor diagnostic-settings delete --name default --resource ${RESOURCE_NAME} --resource-group ${RG_NAME} --resource-type ${RESOURCE_TYPE}
        fi
    done

    echo "Removing resource group ${RG_NAME}"
    az group delete --name ${RG_NAME} --yes
fi

# Delete the network resource group if it exists

DEPLOY_NETWORK=$(yq eval ".deploy_network" ${CONFIG_FILE})
RG_NAME=$(yq eval ".rg_network_name" ${CONFIG_FILE})
RG_EXISTS=$(az group exists --name ${RG_NAME})

if $DEPLOY_NETWORK && $RG_EXISTS
then 
    echo "Removing resource group ${RG_NAME}"
    az group delete --name ${RG_NAME} --yes
fi

# Purge the soft deleted keyvault instance if it exists

KEYVAULT_NAME=$(yq eval ".keyvault_name" ${CONFIG_FILE})
KEYVAULT_SOFT_DELETED_NAME=$(az keyvault list-deleted --query "[?contains(@.name,'${KEYVAULT_NAME}')==\`true\`]".name -o tsv)

if [ ! -z "$KEYVAULT_SOFT_DELETED_NAME" ]
then
    echo "Purging keyvault instance ${KEYVAULT_NAME}"
    az keyvault purge --name ${KEYVAULT_NAME}
fi