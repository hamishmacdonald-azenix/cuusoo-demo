resource "azurerm_service_plan" "app" {
  count               = local.variable["deploy_app"] ? 1 : 0
  name                = local.variable["asp_name"]
  resource_group_name = azurerm_resource_group.app[0].name
  location            = azurerm_resource_group.app[0].location
  os_type             = "Linux"
  sku_name            = local.variable["asp_sku_size"]
  tags                = local.variable["tags"]
}

resource "azurerm_linux_function_app" "function_app" {
  count                      = local.variable["deploy_app"] ? 1 : 0
  name                       = local.variable["function_app_name"]
  resource_group_name        = azurerm_resource_group.app[0].name
  location                   = azurerm_resource_group.app[0].location
  service_plan_id            = azurerm_service_plan.app[0].id
  storage_account_name       = azurerm_storage_account.app[0].name
  storage_account_access_key = azurerm_storage_account.app[0].primary_access_key
  https_only                 = true
  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = "${azurerm_application_insights.app[0].instrumentation_key}"
    "TEMP_FILE_PATH"                 = "/tmp/"
    "RESOURCE_GROUP_NAME"            = "${azurerm_resource_group.data[0].name}"
    "SUBSCRIPTION_ID"                = "${data.azurerm_client_config.current.subscription_id}"
    "KEYVAULT_NAME"                  = "${local.variable["deploy_keyvault"] ? azurerm_key_vault.data[0].name : null}"
    "DATA_FACTORY_NAME"              = "${local.variable["deploy_datafactory"] ? azurerm_data_factory.data[0].name : null}"
    "DATABRICKS_WORKSPACE_URL"       = "${azurerm_databricks_workspace.data.workspace_url}"
    "DATABRICKS_PAT"                 = "@Microsoft.KeyVault(SecretUri=https://${local.variable["deploy_keyvault"] ? azurerm_key_vault.data[0].name : null}.vault.azure.net/secrets/databricksPATToken/)"
    "STORAGE_ACCOUNT_GENERIC"        = "${local.variable["deploy_storage"] ? azurerm_storage_account.generic[0].name : null}"
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "ENABLE_ORYX_BUILD"              = true
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "1"
  }
  site_config {
    ftps_state = "Disabled"
    always_on  = true
    application_stack {
      python_version = "3.9"
    }
  }
  identity {
    type = "SystemAssigned"
  }

  tags = local.variable["tags"]

  depends_on = [
    azurerm_service_plan.app
  ]
}

# Diagnostics (App Insights)

resource "azurerm_application_insights" "app" {
  count               = local.variable["deploy_app"] && local.variable["deploy_loganalytics"] ? 1 : 0
  name                = local.variable["app_insights_name_function_app"]
  resource_group_name = azurerm_resource_group.admin[0].name
  location            = azurerm_resource_group.admin[0].location
  workspace_id        = azurerm_log_analytics_workspace.data[0].id
  application_type    = "web"
}
