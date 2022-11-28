# Role assignments

# Function App MSI to Data Factory

resource "azurerm_role_assignment" "adf_function" {
  count                = local.variable["deploy_datafactory"] ? 1 : 0
  scope                = azurerm_data_factory.data[0].id
  role_definition_name = "Contributor"
  principal_id         = azurerm_linux_function_app.function_app[0].identity[0].principal_id
}

# Deployment SP to data lake

resource "azurerm_role_assignment" "sp_datalake" {
  count                = local.variable["deploy_datafactory"] ? 1 : 0
  scope                = azurerm_storage_account.datalake[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Data Factory MSI to data lake

resource "azurerm_role_assignment" "adf_datalake" {
  count                = local.variable["deploy_datafactory"] ? 1 : 0
  scope                = azurerm_storage_account.datalake[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.data[0].identity[0].principal_id
}

# Function App MSI to data lake

resource "azurerm_role_assignment" "afa_datalake" {
  count                = local.variable["deploy_app"] ? 1 : 0
  scope                = azurerm_storage_account.datalake[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.function_app[0].identity[0].principal_id
}

# Deployment SP to generic storage

resource "azurerm_role_assignment" "sp_generic" {
  count                = local.variable["deploy_datafactory"] ? 1 : 0
  scope                = azurerm_storage_account.generic[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Function App MSI to generic storage

resource "azurerm_role_assignment" "afa_generic" {
  count                = local.variable["deploy_app"] ? 1 : 0
  scope                = azurerm_storage_account.generic[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.function_app[0].identity[0].principal_id
}

# Storage admins - Data lake

resource "azurerm_role_assignment" "storage_admins_datalake" {
  count                = local.variable["deploy_storage"] ? 1 : 0
  scope                = azurerm_storage_account.datalake[0].id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azuread_group.storage_admin.id
}

resource "azurerm_role_assignment" "storage_admins_generic" {
  count                = local.variable["deploy_storage"] ? 1 : 0
  scope                = azurerm_storage_account.generic[0].id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azuread_group.storage_admin.id
}

resource "azurerm_role_assignment" "storage_databricks_sp" {
  count                = local.variable["deploy_storage"] && local.variable["deploy_app_registrations"] ? 1 : 0
  scope                = azurerm_storage_account.datalake[0].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.databricksapp[0].object_id
}