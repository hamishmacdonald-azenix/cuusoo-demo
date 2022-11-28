resource "azurerm_key_vault" "data" {
  count                      = local.variable["deploy_keyvault"] ? 1 : 0
  name                       = local.variable["keyvault_name"]
  resource_group_name        = azurerm_resource_group.security[0].name
  location                   = azurerm_resource_group.security[0].location
  sku_name                   = local.variable["keyvault_sku"]
  tenant_id                  = local.variable["tenantId"]
  soft_delete_retention_days = 30
  tags                       = local.variable["tags"]

  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    ip_rules                   = length(local.variable["allowed_firewall_ips"]) > 0 && local.variable["deploy_logic_app_consumption"] ? concat(local.variable["allowed_firewall_ips"], data.azurerm_logic_app_workflow.logic_app.connector_outbound_ip_addresses) : local.variable["allowed_firewall_ips"]
    virtual_network_subnet_ids = [azurerm_subnet.databricks_public[0].id, local.variable["deploy_app"] ? azurerm_subnet.app[0].id : null]
  }

  depends_on = [
    azurerm_logic_app_workflow.logic_app
  ]
}

#Terraform SP access policy

resource "azurerm_key_vault_access_policy" "terraform_sp" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set"
  ]
}

# Keyvault Admin access policy

resource "azurerm_key_vault_access_policy" "admin_group" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = data.azuread_group.keyvault_admin.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Recover",
    "Backup",
    "Restore",
    "Purge"
  ]

  key_permissions = [
    "Get",
    "List",
    "Update",
    "Create",
    "Import",
    "Delete",
    "Recover",
    "Backup",
    "Restore",
    "Purge"
  ]

  certificate_permissions = [
    "Get",
    "List",
    "Update",
    "Create",
    "Import",
    "Delete",
    "Recover",
    "Backup",
    "Restore",
    "Purge"
  ]
}

# Data Factory MSI access policy

resource "azurerm_key_vault_access_policy" "data_factory" {
  count        = local.variable["deploy_datafactory"] && local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = azurerm_data_factory.data[0].identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}


# Function app MSI access policy

resource "azurerm_key_vault_access_policy" "function_app" {
  count        = local.variable["deploy_app"] && local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = azurerm_linux_function_app.function_app[0].identity[0].principal_id

  secret_permissions = [
    "Get"
  ]
}

# Logic app MSI access policy

resource "azurerm_key_vault_access_policy" "Logic_app_standard" {
  count        = local.variable["deploy_logic_app_standard"] && local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = azurerm_logic_app_standard.logic_app[0].identity[0].principal_id

  secret_permissions = [
    "Get"
  ]
}

resource "azurerm_key_vault_access_policy" "Logic_app_consumption" {
  count        = local.variable["deploy_logic_app_consumption"] && local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = azurerm_logic_app_workflow.logic_app[0].identity[0].principal_id

  secret_permissions = [
    "Get"
  ]
}

# Databricks built in MSI

resource "azurerm_key_vault_access_policy" "databricks_builtin_sp" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  tenant_id    = local.variable["tenantId"]
  object_id    = data.azuread_service_principal.databricks_builtin.object_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# Resources for random secrets

resource "random_password" "special_password" {
  for_each = local.variable["keyvault_secret_list_special"]
  length   = 30
  special  = true

  keepers = {
    name = each.key
  }
}

resource "random_password" "password" {
  for_each = local.variable["keyvault_secret_list_no_special"]
  length   = 30
  special  = false

  keepers = {
    name = each.key
  }
}

# Create automated KeyVault secrets - Special characters

resource "azurerm_key_vault_secret" "secret_special" {
  key_vault_id = azurerm_key_vault.data[0].id
  for_each     = local.variable["keyvault_secret_list_special"]
  name         = each.key
  value        = each.value == "" || each.value == "regenerate" ? random_password.special_password[each.key].result : each.value

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

# Create automated KeyVault secrets - No special characters

resource "azurerm_key_vault_secret" "secret" {
  key_vault_id = azurerm_key_vault.data[0].id
  for_each     = local.variable["keyvault_secret_list_no_special"]
  name         = each.key
  value        = each.value == "" || each.value == "regenerate" ? random_password.password[each.key].result : each.value

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

# Push the secrets derived from the Terraform deployment

resource "azurerm_key_vault_secret" "storageAccountDataLake" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "storageAccountDataLake"
  value        = azurerm_storage_account.datalake[0].name

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "storageAccountGeneric" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "storageAccountGeneric"
  value        = azurerm_storage_account.generic[0].name

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "storageAccountGenericKey" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "storageAccountGenericKey"
  value        = azurerm_storage_account.generic[0].primary_access_key

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "storageAccountDataLakeKey" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "storageAccountDataLakeKey"
  value        = azurerm_storage_account.datalake[0].primary_access_key

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "databricksApplicationID" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "databricksApplicationID"
  value        = azuread_application.databricksapp[0].application_id

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "databricksApplicationKey" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_storage"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "databricksApplicationKey"
  value        = azuread_service_principal_password.databricksapp[0].value

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "functionAppBaseURL" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_app"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "functionAppBaseURL"
  value        = "https://${azurerm_linux_function_app.function_app[0].name}.azurewebsites.net"

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "functionAppFunctionKey" {
  count        = local.variable["deploy_keyvault"] && local.variable["deploy_app"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "functionAppFunctionKey"
  value        = data.azurerm_function_app_host_keys.app.default_function_key

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "databricksBaseURL" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "databricksBaseURL"
  value        = azurerm_databricks_workspace.data.workspace_url

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

resource "azurerm_key_vault_secret" "tenantID" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "tenantID"
  value        = local.variable["tenantId"]

  depends_on = [
    azurerm_key_vault_access_policy.terraform_sp
  ]
}

# Databricks PAT Token

resource "azurerm_key_vault_secret" "databricksPATToken" {
  count        = local.variable["deploy_keyvault"] ? 1 : 0
  key_vault_id = azurerm_key_vault.data[0].id
  name         = "databricksPATToken"
  value        = databricks_token.pat.token_value

  depends_on = [
    databricks_token.pat
  ]
}

# Diagnostics

module "keyvault_diagnostics" {
  count                      = local.variable["deploy_keyvault"] && local.variable["deploy_loganalytics"] ? 1 : 0
  source                     = "./diagnostics"
  diagnostic_setting_name    = local.variable["diagnostic_setting_name"]
  retention_days             = local.variable["diagnostic_retention_days"]
  target_resource_id         = azurerm_key_vault.data[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.data[0].id
  destinaton_type            = "Dedicated"
  depends_on = [
    azurerm_log_analytics_workspace.data
  ]
}
