# Data lake storage account

resource "azurerm_storage_account" "datalake" {
  count                    = local.variable["deploy_storage"] ? 1 : 0
  name                     = local.variable["storage_account_name_datalake"]
  resource_group_name      = azurerm_resource_group.data[0].name
  location                 = azurerm_resource_group.data[0].location
  account_tier             = "Standard"
  account_kind             = "StorageV2"
  account_replication_type = local.variable["storage_replication"]
  is_hns_enabled           = true
  tags                     = local.variable["tags"]

  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = length(local.variable["allowed_firewall_ips"]) > 0 ? local.variable["allowed_firewall_ips"] : []
    virtual_network_subnet_ids = [azurerm_subnet.databricks_public[0].id, azurerm_subnet.app[0].id]
  }

  blob_properties {
    delete_retention_policy {
      days = 30
    }    
    container_delete_retention_policy {
      days = 30
    }
  }
}

# Generic storage account

resource "azurerm_storage_account" "generic" {
  count                    = local.variable["deploy_storage"] ? 1 : 0
  name                     = local.variable["storage_account_name_generic"]
  resource_group_name      = azurerm_resource_group.data[0].name
  location                 = azurerm_resource_group.data[0].location
  account_tier             = "Standard"
  account_kind             = "StorageV2"
  account_replication_type = local.variable["storage_replication"]
  is_hns_enabled           = false
  tags                     = local.variable["tags"]

  blob_properties {
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
    versioning_enabled = true 
  }
}

# Generic containers

resource "azurerm_storage_container" "config" {
  count                 = local.variable["deploy_storage"] ? 1 : 0
  name                  = "config"
  storage_account_name  = azurerm_storage_account.generic[0].name
  container_access_type = "private"
}

# Function app storage - Updated to allow all traffic due to logic apps having an issue accessing storage behind a firewall

resource "azurerm_storage_account" "app" {
  count                    = local.variable["deploy_storage"] ? 1 : 0
  name                     = local.variable["storage_account_name_app"]
  resource_group_name      = azurerm_resource_group.data[0].name
  location                 = azurerm_resource_group.data[0].location
  account_tier             = "Standard"
  account_kind             = "StorageV2"
  account_replication_type = "GRS"
  is_hns_enabled           = false
  tags                     = local.variable["tags"]

  # network_rules {
  #   default_action             = "Deny"
  #   bypass                     = ["AzureServices"]
  #   virtual_network_subnet_ids = [azurerm_subnet.app[0].id, azurerm_subnet.logic_app[0].id]
  # }
}

# Data lake file system

resource "azurerm_storage_data_lake_gen2_filesystem" "data_lake" {
  count              = local.variable["deploy_storage"] ? 1 : 0
  name               = local.variable["datalake_file_system_name"]
  storage_account_id = azurerm_storage_account.datalake[0].id
  depends_on = [
    azurerm_storage_account.datalake
  ]
}

# Diagnostics

module "datalake_diagnostics" {
  count                      = local.variable["deploy_storage"] && local.variable["deploy_loganalytics"] ? 1 : 0
  source                     = "./diagnostics"
  diagnostic_setting_name    = local.variable["diagnostic_setting_name"]
  retention_days             = local.variable["diagnostic_retention_days"]
  target_resource_id         = azurerm_storage_account.datalake[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.data[0].id
  destinaton_type            = "Dedicated"
  depends_on = [
    azurerm_log_analytics_workspace.data
  ]
}