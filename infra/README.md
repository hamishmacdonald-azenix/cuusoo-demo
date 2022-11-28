# Infrastructure as Code (IaC)

All the infrastructure deployed into the customers environment is done via a single Terraform project, using YAML configuration files that are decoded and used a local variables in the project. Create a separate YAML configuration file for each environment, following the convention `infra-<environment name>.yaml`.

The table below details the various sections in the YAML configuration files:

| Section Title | Description |
| -------------- | ----------- |
| **Azure deployment settings** | The Azure service principal client ID, tenant ID and subscription that are being deployed into |
| **Terraform config** | The Terraform configuration items used for the project initialisation |
| **Boolean indicators** | These indicators are to be set to `true` or `false`, depending on which resources need to be deployed as part of the solution. <br><br>If the customer has their own network, set `deploy_network` to `false` and if they plan to create all Azure Active Directory (AAD) groups themselves, set `deploy_groups` to `false` <br><br>If you plan to deploy a consumption-based logic app, set `deploy_logic_app_consumption` to `true` and `deploy_logic_app_standard` to `false`, or the inverse for a standard workflow app |
| **Resource group names** | The names of the resource groups that need to be created and deployed into. You can make these all the same name if the customer requests deploying into a single resource group |
| **Function App** | The details for the deployed function app and related service plan |
| **Logic App** | The details for the deployed logic app and related service plan |
| **Networking** | The details for the new or existing vNet that is to be deployed into. The solution requires 4 subnets per environment: <br><li> 2 for Databricks (`subnet_public` and `subnet_private`, at least /26) <li> 1 for the app service plan (`app_subnet`, at least /27) <li> 1 for the logic app (`logic_app`, at least /27) |
| **Public IP** | Used an the public IP exposed through the NAT gateway that sits in front of the Databricks public subnet, to direct all external traffic from the Databricks service |
| **NAT gateway** | NAT gateway details for the Databricks public network traffic |
| **Allowed firewall IPs** | A comma-separated list of public IP addresses that are allowed in the deployed Key Vault and storage account firewall rules. These are typically the fixed IP's assigned to customer firewalls or VPN's |
| **Storage** | Storage account details for the generic storage account and the deployed data lake |
| **Databricks** | Databricks workspace settings and managed resource group names |
| **Keyvault** | The name of the deployed Key Vault instance |
| **Data Factory** | Name of the deta factory instance |
| **Git Integration** | Allows you to configure Git integration for the deployed Data Factory instance |
| **Managed private endpoints** | Managed private endpoint connections for Azure Data Factory |
| **Log Analytics** | Log analytics workspace details |
| **Azure AD Groups** | The names assigned to the Azure AD groups. These include: <br><li>Key Vault administrators<br><li>Storage administrators<br><li>Databricks users<br><li>Databricks administrators |
| **Azure Monitor Action Groups** | The name and email address for an action group to which emails will sent if ADF pipelines experience a failure. Set the value to an empty list `[]` if not required |
| **Azure AD App Registrations** | The name of the app registration created for use by Databricks to authenticate with the underlying data lake storage account |
| **General config** | Specify the location for all resources and an array of tags that are to be added to all deployed resources |
| **Diagnostics settings** | The default retention period and name given to diagnostics settings configured for various Azure services |
| **KeyVault secret list** | Houses the list of Key Vault secrets which either do not contain sensitive information, or have reandomly generated values, such as virtual machine administrative passwords |

## Local development

### Prerequisites

To get started, ensure you have the tools below installed on your local machine: 
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Terraform CLI](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- [jq](https://stedolan.github.io/jq/download/)
- [yq](https://github.com/mikefarah/yq#install)

To ensure that the relevant Terraform state file resource groups, storage accounts and state files exist, run the [terraform-backend.sh](infra/scripts/terraform-backend.sh) for each separate configuration, ensuring you set a local variable named `TARGET_CONFIG` to the name of the configuration file you are using, given the example below:

```bash
export TARGET_CONFIG="infra-config-demo"
```

Once all the backed resources have been created, you can initialise the Terraform project by executing the [terraform-init.sh](infra/scripts/terraform-init.sh) script for each config file, ensuring you set the environment variable above for each separate config.

### Additional environment varibles

Ensure the local variables below are set before running `terraform plan` and `terraform apply` commands:

- **ARM_CLIENT_ID** - The client ID for the service principal used to deploy into Azure
- **ARM_CLIENT_SECRET** - The client secret for the service principal used to deploy into Azure
- **ARM_TENANT_ID** - The Azure tenancy ID that is being deployed into
- **ARM_SUBSCRIPTION_ID** - The Azure subscription that is being deployed into

## Deployment

Ensure the same local variables as above are set in your DevOps tool of choice. Include `terraform plan` and `terraform apply` commands in your pipeline, making sure to include a manual approval step between development and production deployment stages, if required.

There are some additional steps required for deployment, some being one-off and others required for each deployment.

### One-off tasks

At present, it is not possible to deploy a Key Vault-backed secret scope using a service principal (details [here](https://registry.terraform.io/providers/databrickslabs/databricks/latest/docs/resources/secret_scope#keyvault_metadata)). As such, you will need to run an `az login --tenant <tenant ID>` to perform an interactive login into Azure using a credential which has contributor access over the resource group/s that the solution is being deployed to. 

Once you have logged in, run the command below from the command line, ensuring the correct `TARGET_CONFIG` environment varible has been set, in addition to all the `ARM_` environment variables:

```bash
./databricks-keyvault-secret-scope.sh 
```

### Ongoing tasks

To ensure the deployed Key Vault instance remain secure, firewall rules block unwanted external IP addresses, preventing a DevOps agent (Or local machine), from accessing the Key Vault instance by default.

To circumvent this restriction and provide temporary firewall access to the Key Vault instance, the [open-close-firewall.sh](infra/scripts/open-close-firewall.sh) Bash script was created, to temporarily open the firewall before running `terraform plan` and `terraform apply` commands.

To use the script, ensure all the required environment variables above have been set, and execute the command below from the command line:

```bash
./scripts/open-close-firewall.sh Operation Rule_Type
```

where 

- **Operation** is `open` to open the firewall and `close` to close it
- **Rule_Type** is `ip`

If you deploy a self-hosted CI/CD agent into Azure or the customer already has one, you can specify `subnet` as the rule type instead, which will temporarily open the Key Vault instance to the agent subnet through a service endpoint.