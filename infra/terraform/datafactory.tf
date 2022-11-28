resource "azurerm_data_factory" "data" {
  count               = local.variable["deploy_datafactory"] ? 1 : 0
  name                = local.variable["data_factory_name"]
  resource_group_name = azurerm_resource_group.data[0].name
  location            = azurerm_resource_group.data[0].location
  managed_virtual_network_enabled = true
  tags                = local.variable["tags"]

  identity {
    type = "SystemAssigned"
  }

  dynamic "vsts_configuration" {
    for_each = local.variable["deploy_datafactory_vsts"] ? [1] : []
    content {
      account_name      = local.variable["adf_vsts_account_name"]
      branch_name       = local.variable["adf_vsts_branch_name"]
      project_name      = local.variable["adf_vsts_project_name"]
      repository_name   = local.variable["adf_vsts_repository_name"]
      root_folder       = local.variable["adf_vsts_root_folder"]
      tenant_id         = local.variable["tenantId"]
    }
  }

  global_parameter {
    name  = "keyVaultURI"
    type  = "String"
    value = local.variable["deploy_keyvault"] ? azurerm_key_vault.data[0].vault_uri : null
  }
}

# Diagnostics

module "datafactory_diagnostics" {
  count                      = local.variable["deploy_datafactory"] && local.variable["deploy_loganalytics"] ? 1 : 0
  source                     = "./diagnostics"
  diagnostic_setting_name    = local.variable["diagnostic_setting_name"]
  retention_days             = local.variable["diagnostic_retention_days"]
  target_resource_id         = azurerm_data_factory.data[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.data[0].id
  destinaton_type            = "Dedicated"
  depends_on = [
    azurerm_log_analytics_workspace.data
  ]
}

# Pipeline alerts

resource "azurerm_monitor_metric_alert" "pipeline_failure" {
  count               = local.variable["deploy_datafactory"] && local.variable["deploy_datafactory_alerts"] ? 1 : 0
  name                = "Failed Pipeline Runs - ${azurerm_data_factory.data[0].name}"
  resource_group_name = azurerm_resource_group.data[0].name
  scopes              = [azurerm_data_factory.data[0].id]
  description         = "Action will be triggered when failed pipelines is greater than 0"
  frequency           = "PT1H"
  window_size         = "PT1H"
  severity            = 3

  criteria {
    metric_namespace = "Microsoft.DataFactory/factories"
    metric_name      = "PipelineFailedRuns"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = data.azurerm_monitor_action_group.dp_admin[0].id
  }
}
