resource "azurerm_service_plan" "logic_app" {
  count               = local.variable["deploy_logic_app_standard"] ? 1 : 0
  name                = local.variable["logic_asp_name"]
  resource_group_name = azurerm_resource_group.app[0].name
  location            = azurerm_resource_group.app[0].location
  os_type             = "Windows"
  sku_name            = local.variable["logic_asp_sku_size"]
  tags                = local.variable["tags"]
}

# Standard logic app

resource "azurerm_logic_app_standard" "logic_app" {
  count                      = local.variable["deploy_logic_app_standard"] ? 1 : 0
  name                       = local.variable["logic_app_name"]
  resource_group_name        = azurerm_resource_group.app[0].name
  location                   = azurerm_resource_group.app[0].location
  app_service_plan_id        = azurerm_service_plan.logic_app[0].id
  storage_account_name       = azurerm_storage_account.app[0].name
  storage_account_access_key = azurerm_storage_account.app[0].primary_access_key
  storage_account_share_name = join("-", [local.variable["logic_app_name"], "share"])
  https_only                 = true
  version                    = "~3"
  tags                       = local.variable["tags"]
  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = "${azurerm_application_insights.logic_app[0].instrumentation_key}"
    "RESOURCE_GROUP_NAME"            = "${azurerm_resource_group.data[0].name}"
    "SUBSCRIPTION_ID"                = "${data.azurerm_client_config.current.subscription_id}"
    "DATABRICKS_WORKSPACE_URL"       = "${azurerm_databricks_workspace.data.workspace_url}"
    "DATA_FACTORY_NAME"              = "${local.variable["deploy_datafactory"] ? azurerm_data_factory.data[0].name : null}"
    "DATABRICKS_PAT"                 = "@Microsoft.KeyVault(SecretUri=https://${local.variable["deploy_keyvault"] ? azurerm_key_vault.data[0].name : null}.vault.azure.net/secrets/databricksPATToken/)"
    "FUNCTIONS_WORKER_RUNTIME"       = "node"
    "WEBSITE_NODE_DEFAULT_VERSION"   = "~12"
  }
  site_config {
    ftps_state                = "Disabled"
    ip_restriction            = []
    dotnet_framework_version  = "v4.0"
    app_scale_limit           = 0
    elastic_instance_minimum  = 1
    pre_warmed_instance_count = 1
  }
  identity {
    type = "SystemAssigned"
  }

  depends_on = [
    azurerm_service_plan.logic_app
  ]
}

# Consumption Logic App

resource "azurerm_logic_app_workflow" "logic_app" {
  count                      = local.variable["deploy_logic_app_consumption"] ? 1 : 0
  name                       = local.variable["logic_app_name"]
  resource_group_name        = azurerm_resource_group.app[0].name
  location                   = azurerm_resource_group.app[0].location
  tags                       = local.variable["tags"]
  identity {
    type = "SystemAssigned"
  }
}

# Keyvault API connection for Consumption Logic App

resource "azurerm_api_connection" "keyvault" {
  count               = local.variable["deploy_logic_app_consumption"] && local.variable["deploy_keyvault"] ? 1 : 0
  name                = "keyvault"
  resource_group_name = azurerm_resource_group.app[0].name
  managed_api_id      = data.azurerm_managed_api.keyvault.id
  display_name        = "keyvault"
  tags = local.variable["tags"]
}

# Diagnostics (App Insights)

resource "azurerm_application_insights" "logic_app" {
  count               = (local.variable["deploy_logic_app_standard"] || local.variable["deploy_logic_app_consumption"]) && local.variable["deploy_loganalytics"] ? 1 : 0
  name                = local.variable["app_insights_name_logic_app"]
  resource_group_name = azurerm_resource_group.admin[0].name
  location            = azurerm_resource_group.admin[0].location
  workspace_id        = azurerm_log_analytics_workspace.data[0].id
  application_type    = "web"
}
