# Create the Azure AD groups

resource "azuread_group" "keyvault_admin" {
  count            = local.variable["deploy_groups"] ? 1 : 0
  display_name     = local.variable["keyvault_admin_group_name"]
  owners           = [data.azurerm_client_config.current.object_id]
  members          = []
  security_enabled = true
}

resource "azuread_group" "storage_admin" {
  count            = local.variable["deploy_groups"] ? 1 : 0
  display_name     = local.variable["storage_admin_group_name"]
  owners           = [data.azurerm_client_config.current.object_id]
  members          = []
  security_enabled = true
}

resource "azuread_group" "databricks_users" {
  count            = local.variable["deploy_groups"] ? 1 : 0
  display_name     = local.variable["databricks_users_group_name"]
  owners           = [data.azurerm_client_config.current.object_id]
  members          = []
  security_enabled = true
}

resource "azuread_group" "databricks_admins" {
  count            = local.variable["deploy_groups"] ? 1 : 0
  display_name     = local.variable["databricks_admin_users_group_name"]
  owners           = [data.azurerm_client_config.current.object_id]
  members          = []
  security_enabled = true
}

# Create the Databricks service principal for storage account authenticaton

resource "time_rotating" "annual" {
  rotation_days = 360
}

resource "azuread_application" "databricksapp" {
  count        = local.variable["deploy_app_registrations"] ? 1 : 0
  display_name = local.variable["databricks_app_name"]
  owners       = [data.azurerm_client_config.current.object_id]
}

resource "azuread_service_principal" "databricksapp" {
  count                        = local.variable["deploy_app_registrations"] ? 1 : 0
  application_id               = azuread_application.databricksapp[0].application_id
  app_role_assignment_required = false
  owners                       = [data.azurerm_client_config.current.object_id]
}

resource "azuread_service_principal_password" "databricksapp" {
  count                = local.variable["deploy_app_registrations"] ? 1 : 0
  service_principal_id = azuread_service_principal.databricksapp[0].object_id
  rotate_when_changed = {
    rotation = time_rotating.annual.id
  }
}