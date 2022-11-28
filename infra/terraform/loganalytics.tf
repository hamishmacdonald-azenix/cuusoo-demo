resource "azurerm_log_analytics_workspace" "data" {
  count               = local.variable["deploy_loganalytics"] ? 1 : 0
  name                = local.variable["log_analytics_name"]
  resource_group_name = azurerm_resource_group.admin[0].name
  location            = azurerm_resource_group.admin[0].location
  sku                 = local.variable["log_analytics_sku"]
  retention_in_days   = local.variable["log_analytics_retention"]
  tags                = local.variable["tags"]
}