# Databricks provider not in use while creating a KeyVault backed secret scope is unsupported 
# using Service Principal authentication
# https://registry.terraform.io/providers/databrickslabs/databricks/latest/docs/resources/secret_scope#keyvault_metadata

terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "=2.25.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.12.0"
    }
    databricks = {
      source = "databricks/databricks"
      version = "=1.0.0"
    }
    random = {
      source = "hashicorp/random"
      version = "=3.3.1"
    }
  }
  backend "azurerm" {
      resource_group_name  = "rg-westrac-demo-tfs"
      storage_account_name = "wtdemotfs"
      container_name       = "tfstate"
      key = "infra-westrac-demo.state"
    }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }    
}

provider "databricks" {
  alias                       = "default_databricks"
  host                        = azurerm_databricks_workspace.data.workspace_url
  azure_workspace_resource_id = azurerm_databricks_workspace.data.id
}