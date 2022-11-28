# Azure AD objects

data "azuread_service_principal" "databricks_builtin" {
  application_id = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
}

data "azuread_group" "keyvault_admin" {
  display_name = local.variable["keyvault_admin_group_name"]
  depends_on = [
    azuread_group.keyvault_admin
  ]
}

data "azuread_group" "storage_admin" {
  display_name = local.variable["storage_admin_group_name"]
  depends_on = [
    azuread_group.storage_admin
  ]
}

# Networking

data "azurerm_virtual_network" "databricks_vnet" {
  name                = local.variable["vnet_name"]
  resource_group_name = local.variable["rg_network_name"]
  depends_on          = [
    azurerm_virtual_network.databricks_vnet
  ]
}

data "azurerm_network_security_group" "databricks_nsg" {
  name                = local.variable["nsg_name"]
  resource_group_name = local.variable["rg_network_name"]
  depends_on          = [
    azurerm_network_security_group.databricks_nsg
  ]
}

# Function app keys

data "azurerm_function_app_host_keys" "app" {
  name                = local.variable["function_app_name"]
  resource_group_name = azurerm_resource_group.app[0].name
  depends_on          = [
    azurerm_linux_function_app.function_app
  ]
}

# Standard logic app

data "azurerm_logic_app_standard" "logic_app" {
  name                = local.variable["logic_app_name"]
  resource_group_name = azurerm_resource_group.app[0].name
  depends_on          = [
    azurerm_logic_app_standard.logic_app
  ]
}

# Workflow logic app

data "azurerm_logic_app_workflow" "logic_app" {
  name                = local.variable["logic_app_name"]
  resource_group_name = azurerm_resource_group.app[0].name
  depends_on          = [
    azurerm_logic_app_workflow.logic_app
  ]
}

# Keyvault managed API

data "azurerm_managed_api" "keyvault" {
  name     = "keyvault"
  location = azurerm_resource_group.security[0].location
}

data "azurerm_client_config" "current" {}

# Diagnostics

data "azurerm_monitor_diagnostic_categories" "keyvault" {
  resource_id = azurerm_key_vault.data[0].id
  depends_on = [
    azurerm_key_vault.data
  ]
}

data "azurerm_monitor_diagnostic_categories" "databricks" {
  resource_id = azurerm_databricks_workspace.data.id
}

data "azurerm_monitor_diagnostic_categories" "datafactory" {
  resource_id = azurerm_data_factory.data[0].id
  depends_on = [
    azurerm_data_factory.data
  ]
}

data "azurerm_monitor_diagnostic_categories" "datalake" {
  resource_id = azurerm_storage_account.datalake[0].id
  depends_on = [
    azurerm_storage_account.datalake
  ]
}

# Azure monitor actions groups

data "azurerm_monitor_action_group" "dp_admin" {
  count               = length(local.variable["action_groups"]) > 0 ? 1 : 0
  resource_group_name = azurerm_resource_group.admin[0].name
  name                = "DPAdminActionGroup"
  depends_on = [
    azurerm_monitor_action_group.action_groups
  ]
}