data "azurerm_monitor_diagnostic_categories" "this" {
  resource_id = var.target_resource_id
}

resource "azurerm_monitor_diagnostic_setting" "this" {
  name                           = var.diagnostic_setting_name
  target_resource_id             = var.target_resource_id
  log_analytics_workspace_id     = var.log_analytics_workspace_id != "" ? var.log_analytics_workspace_id : null
  storage_account_id             = var.storage_account_id != "" ? var.eventhub_authorization_rule_id : null
  eventhub_authorization_rule_id = var.eventhub_authorization_rule_id != "" ? var.eventhub_authorization_rule_id : null
  log_analytics_destination_type = var.destinaton_type != "" ? var.destinaton_type : null

  dynamic "log" {
    for_each = data.azurerm_monitor_diagnostic_categories.this.logs
    content {
      category = log.value
      enabled  = true
      retention_policy {
        days    = var.retention_days
        enabled = var.retention_days > 0 ? true : false
      }
    }
  }

  dynamic "metric" {
    for_each = data.azurerm_monitor_diagnostic_categories.this.metrics
    content {
      category = metric.value
      enabled  = true
      retention_policy {
        days    = var.retention_days
        enabled = var.retention_days > 0 ? true : false
      }
    }
  }
}
