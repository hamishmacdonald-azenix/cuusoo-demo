resource "azurerm_databricks_workspace" "data" {
  name                = local.variable["databricks_workspace_name"]
  resource_group_name = azurerm_resource_group.data[0].name
  location            = azurerm_resource_group.data[0].location
  managed_resource_group_name = local.variable["databricks_managed_resource_group_name"]
  sku                 = local.variable["databricks_sku"]
  tags                = local.variable["tags"]
  custom_parameters {
    virtual_network_id                                   = data.azurerm_virtual_network.databricks_vnet.id
    public_subnet_name                                   = local.variable["subnet_public_name"]
    private_subnet_name                                  = local.variable["subnet_private_name"]
    public_subnet_network_security_group_association_id  = data.azurerm_network_security_group.databricks_nsg.id
    private_subnet_network_security_group_association_id = data.azurerm_network_security_group.databricks_nsg.id
    nat_gateway_name                                     = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? azurerm_nat_gateway.databricks_nat_gateway[0].name : null
    public_ip_name                                       = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? azurerm_public_ip.databricks_public[0].name : null
    no_public_ip                                         = local.variable["deploy_databricks_ssc"]
    storage_account_sku_name                             = "Standard_LRS" 
  }
  depends_on = [
    azurerm_network_security_group.databricks_nsg,
    azurerm_subnet.databricks_private,
    azurerm_subnet.databricks_public,
    azurerm_subnet_network_security_group_association.databricks_public,
    azurerm_subnet_network_security_group_association.databricks_private,
  ]
}

# KeyVault secret scope - Currently not supported using a service principal for authentication
# https://registry.terraform.io/providers/databrickslabs/databricks/latest/docs/resources/secret_scope#keyvault_metadata

# resource "databricks_secret_scope" "keyvault" {
#   count = local.variable["deploy_keyvault"] ? 1 : 0
#   name  = local.variable["keyvault_scope_name"]

#   keyvault_metadata {
#     resource_id = azurerm_key_vault.data[0].id
#     dns_name    = azurerm_key_vault.data[0].vault_uri
#   }
# }

# Create the PAT token for push to Key Vault
resource "databricks_token" "pat" {
  provider = databricks.default_databricks
  comment  = "Terraform Provisioning"
  # Exclude lifetime to make it indefinite
  # lifetime_seconds = 8640000
}

# Diagnostics

# module "databricks_diagnostics" {
#   source                     = "./diagnostics"
#   diagnostic_setting_name    = local.variable["diagnostic_setting_name"]
#   retention_days             = local.variable["diagnostic_retention_days"]
#   target_resource_id         = azurerm_databricks_workspace.data.id
#   log_analytics_workspace_id = azurerm_log_analytics_workspace.data[0].id
#   destinaton_type            = "Dedicated"
#   depends_on = [
#     azurerm_log_analytics_workspace.data
#   ]
# }