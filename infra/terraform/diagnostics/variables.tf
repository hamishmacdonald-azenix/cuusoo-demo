variable "target_resource_id" {
  description = <<-EOT
    (Required) The resource ID of the resource to enable diagnostic settings
    on.
  EOT
  type        = string
}

variable "diagnostic_setting_name" {
  description = <<-EOT
    (Required) The name of the diagnostic
    setting.
  EOT
  type        = string
  default     = ""
}

variable "log_analytics_workspace_id" {
  description = <<-EOT
    (Optional) The resource ID of the log analytics workspace to send logs to. One of
    log_analytics_workspace_id, storage_account_id or eventhub_authorization_rule_id must be
    provided.
  EOT
  type        = string
  default     = ""
}

variable "storage_account_id" {
  description = <<-EOT
    (Optional) The resource ID of the storage account to send logs to. One of
    log_analytics_workspace_id, storage_account_id or eventhub_authorization_rule_id must be
    provided.
  EOT
  type        = string
  default     = ""
}

variable "eventhub_authorization_rule_id" {
  description = <<-EOT
    (Optional) The resource ID of the event hub authorization rule to send logs to. One of
    log_analytics_workspace_id, storage_account_id or eventhub_authorization_rule_id must be
    provided.
  EOT
  type        = string
  default     = ""
}

variable "destinaton_type" {
  description = <<-EOT
    (Optional) When set to 'Dedicated' logs sent to a Log Analytics workspace will go into 
    resource specific tables, instead of the legacy AzureDiagnostics table.
  EOT
  type        = string
  default     = ""
}

variable "retention_days" {
  description = <<-EOT
    (Optional) When set to 0, log rention will be 
    indefinite.
  EOT
  type        = number
  default     = 0
}
