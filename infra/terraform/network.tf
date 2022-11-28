# Databricks vNet and subnets

resource "azurerm_virtual_network" "databricks_vnet" {
  count               = local.variable["deploy_network"] ? 1 : 0
  name                = local.variable["vnet_name"]
  resource_group_name = azurerm_resource_group.network[0].name
  location            = azurerm_resource_group.network[0].location
  address_space       = [local.variable["vnet_cidr"]]
  tags                = local.variable["tags"]
}

resource "azurerm_subnet" "databricks_public" {
  count                = local.variable["deploy_network"] ? 1 : 0
  name                 = local.variable["subnet_public_name"]
  virtual_network_name = azurerm_virtual_network.databricks_vnet[0].name
  resource_group_name  = azurerm_resource_group.network[0].name
  address_prefixes     = [local.variable["subnet_public_cidr"]]
  service_endpoints    = ["Microsoft.Storage", "Microsoft.KeyVault"]

  delegation {
    name = format("%s-databricks-delegation", local.variable["subnet_public_name"])

    service_delegation {
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action",
      ]
      name = "Microsoft.Databricks/workspaces"
    }
  }
}

resource "azurerm_subnet" "databricks_private" {
  count                = local.variable["deploy_network"] ? 1 : 0
  name                 = local.variable["subnet_private_name"]
  virtual_network_name = azurerm_virtual_network.databricks_vnet[0].name
  resource_group_name  = azurerm_resource_group.network[0].name
  address_prefixes     = [local.variable["subnet_private_cidr"]]

  delegation {
    name = format("%s-databricks-delegation", local.variable["subnet_private_name"])

    service_delegation {
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action",
      ]
      name = "Microsoft.Databricks/workspaces"
    }
  }
}

# Databricks NSG

resource "azurerm_network_security_group" "databricks_nsg" {
  count               = local.variable["deploy_network"] ? 1 : 0
  name                = local.variable["nsg_name"]
  location            = azurerm_resource_group.network[0].location
  resource_group_name = azurerm_resource_group.network[0].name
  depends_on = [
    azurerm_subnet.databricks_public, azurerm_subnet.databricks_private
  ]
  tags = local.variable["tags"]
}

resource "azurerm_subnet_network_security_group_association" "databricks_public" {
  count                     = local.variable["deploy_network"] ? 1 : 0
  subnet_id                 = azurerm_subnet.databricks_public[0].id
  network_security_group_id = azurerm_network_security_group.databricks_nsg[0].id
}

resource "azurerm_subnet_network_security_group_association" "databricks_private" {
  count                     = local.variable["deploy_network"] ? 1 : 0
  subnet_id                 = azurerm_subnet.databricks_private[0].id
  network_security_group_id = azurerm_network_security_group.databricks_nsg[0].id
}

# Databricks public IP for NAT

resource "azurerm_public_ip" "databricks_public" {
  count               = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  name                = local.variable["public_ip_name"]
  resource_group_name = azurerm_resource_group.network[0].name
  location            = azurerm_resource_group.network[0].location
  allocation_method   = "Static"
  sku                 = local.variable["public_ip_sku"]
}

resource "azurerm_public_ip_prefix" "databricks_public" {
  count               = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  name                = local.variable["public_ip_prefix_name"]
  resource_group_name = azurerm_resource_group.network[0].name
  location            = azurerm_resource_group.network[0].location
  prefix_length       = 30
}

# NAT gateway

resource "azurerm_nat_gateway" "databricks_nat_gateway" {
  count               = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  name                = local.variable["nat_gateway_name"]
  resource_group_name = azurerm_resource_group.network[0].name
  location            = azurerm_resource_group.network[0].location
  tags                = local.variable["tags"]
}

# Attach NAT gateway to Databricks subnets

resource "azurerm_subnet_nat_gateway_association" "databricks_public" {
  count          = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  subnet_id      = azurerm_subnet.databricks_public[0].id
  nat_gateway_id = azurerm_nat_gateway.databricks_nat_gateway[0].id
}

resource "azurerm_subnet_nat_gateway_association" "databricks_private" {
  count          = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  subnet_id      = azurerm_subnet.databricks_private[0].id
  nat_gateway_id = azurerm_nat_gateway.databricks_nat_gateway[0].id
}

# Public IPs

resource "azurerm_nat_gateway_public_ip_prefix_association" "databricks" {
  count               = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  nat_gateway_id      = azurerm_nat_gateway.databricks_nat_gateway[0].id
  public_ip_prefix_id = azurerm_public_ip_prefix.databricks_public[0].id
}

resource "azurerm_nat_gateway_public_ip_association" "databricks" {
  count                = local.variable["deploy_network"] && local.variable["deploy_databricks_ssc"] ? 1 : 0
  nat_gateway_id       = azurerm_nat_gateway.databricks_nat_gateway[0].id
  public_ip_address_id = azurerm_public_ip.databricks_public[0].id
}

# Managed private endpoints
/* 
NB! You cannot specify the fqdns when first creating the resources, but it is required for future deployments,
otherwise the managed private endpoints will be deleted.
*/

resource "azurerm_data_factory_managed_private_endpoint" "sql" {
  count              = local.variable["deploy_network"] && local.variable["deploy_datafactory_mpe"] ? 1 : 0
  name               = local.variable["data_factory_mpe_sql"]
  data_factory_id    = azurerm_data_factory.data[0].id
  target_resource_id = local.variable["data_factory_mpe_sql_target_source_id"]
  subresource_name   = local.variable["data_factory_mpe_sql_subresource"]
  fqdns              = local.variable["data_factory_mpe_sql_target_fqdns_required"] ? [local.variable["data_factory_mpe_sql_target_fqdns"]] : []
}

resource "azurerm_data_factory_managed_private_endpoint" "datalake" {
  count              = local.variable["deploy_network"] && local.variable["deploy_datafactory_mpe"] ? 1 : 0
  name               = local.variable["data_factory_mpe_datalake"]
  data_factory_id    = azurerm_data_factory.data[0].id
  target_resource_id = azurerm_storage_account.datalake[0].id
  subresource_name   = local.variable["data_factory_mpe_datalake_subresource"]
  fqdns              = [join("", [azurerm_storage_account.datalake[0].name, ".dfs.core.windows.net"])]
}

resource "azurerm_data_factory_managed_private_endpoint" "keyvault" {
  count              = local.variable["deploy_keyvault"] && local.variable["deploy_datafactory_mpe"] ? 1 : 0
  name               = local.variable["data_factory_mpe_keyvault"]
  data_factory_id    = azurerm_data_factory.data[0].id
  target_resource_id = azurerm_key_vault.data[0].id
  subresource_name   = local.variable["data_factory_mpe_keyvault_subresource"]
  fqdns              = [join("", [azurerm_key_vault.data[0].name, ".vault.azure.net"])]
}

# App service subnet and vNet integration

resource "azurerm_subnet" "app" {
  count                = local.variable["deploy_network"] && local.variable["deploy_app"] ? 1 : 0
  name                 = local.variable["app_subnet_name"]
  virtual_network_name = azurerm_virtual_network.databricks_vnet[0].name
  resource_group_name  = azurerm_resource_group.network[0].name
  address_prefixes     = [local.variable["app_subnet_cidr"]]
  service_endpoints    = ["Microsoft.Storage", "Microsoft.KeyVault"]

  delegation {
    name = format("%s-app-delegation", local.variable["app_subnet_name"])

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_app_service_virtual_network_swift_connection" "app" {
  count          = local.variable["deploy_network"] && local.variable["deploy_app"] ? 1 : 0
  app_service_id = azurerm_linux_function_app.function_app[0].id
  subnet_id      = azurerm_subnet.app[0].id
}

# Logic App service subnet and vNet integration

resource "azurerm_subnet" "logic_app" {
  count                = local.variable["deploy_network"] && local.variable["deploy_logic_app_standard"] ? 1 : 0
  name                 = local.variable["logic_app_subnet_name"]
  virtual_network_name = azurerm_virtual_network.databricks_vnet[0].name
  resource_group_name  = azurerm_resource_group.network[0].name
  address_prefixes     = [local.variable["logic_app_subnet_cidr"]]
  service_endpoints    = ["Microsoft.Storage", "Microsoft.KeyVault"]

  delegation {
    name = format("%s-app-delegation", local.variable["logic_app_subnet_name"])

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_app_service_virtual_network_swift_connection" "logic_app" {
  count          = local.variable["deploy_network"] && local.variable["deploy_logic_app_standard"] ? 1 : 0
  app_service_id = azurerm_logic_app_standard.logic_app[0].id
  subnet_id      = azurerm_subnet.logic_app[0].id
}
