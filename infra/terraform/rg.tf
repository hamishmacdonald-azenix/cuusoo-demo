# Resource Groups

resource "azurerm_resource_group" "data" {
  count    = local.variable["deploy_datafactory"] ? 1 : 0
  name     = local.variable["rg_data_name"]
  location = local.variable["location"]
  tags     = local.variable["tags"]
}

resource "azurerm_resource_group" "admin" {
  count    = local.variable["deploy_loganalytics"] ? 1 : 0
  name     = local.variable["rg_admin_name"]
  location = local.variable["location"]
  tags     = local.variable["tags"]
}

resource "azurerm_resource_group" "security" {
  count    = local.variable["deploy_keyvault"] ? 1 : 0
  name     = local.variable["rg_security_name"]
  location = local.variable["location"]
  tags     = local.variable["tags"]
}

resource "azurerm_resource_group" "network" {
  count    = local.variable["deploy_network"] ? 1 : 0
  name     = local.variable["rg_network_name"]
  location = local.variable["location"]
  tags     = local.variable["tags"]
}

resource "azurerm_resource_group" "app" {
  count    = local.variable["deploy_app"] ? 1 : 0
  name     = local.variable["rg_app_name"]
  location = local.variable["location"]
  tags     = local.variable["tags"]
}