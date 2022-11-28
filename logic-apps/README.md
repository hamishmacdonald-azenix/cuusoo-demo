# Azure Logic App

This folder contains both the consumption-based logic app and standard workflow deployment, used to synchronously execute Databricks jobs via the [Jobs API](https://docs.databricks.com/dev-tools/api/latest/jobs.html). 

The standard workflow is more secure as it integrates with the deployed Key Vault instance via a service endpoint, whereas the consumption-based logic app connects to Key Vault using the outgoing IP address range defined by the logic app itself, opened in the Key Vault firewall rules. The downside is cost - The cheapest standard workflow plan is around $230 AUD / month, which cannot be justified, unless the customer has a number of other logic apps running off of the same plan.

## Local development

To test your code locally, follow [this](https://learn.microsoft.com/en-us/azure/logic-apps/create-single-tenant-workflows-visual-studio-code#tools) guide provided by Microsoft, centered around using VS Code as your IDE. Note that only standard plan logic apps can be debugged locally.

## Deployment

To deploy the logic app to Azure, run the relevant `deploy-logicapp.sh` Bash script, based on the type of logic app you are deploying. The only parameter required for the script is the configuration file that is used for the Terraform deployment, located in the [infra > config](infra/config) folder.

Ensure the local variables below are set before executing the script - These are the same variables required for a Terraform deployment:

- **ARM_CLIENT_ID** - The client ID for the service principal used to deploy into Azure
- **ARM_CLIENT_SECRET** - The client secret for the service principal used to deploy into Azure
- **ARM_TENANT_ID** - The Azure tenancy ID that is being deployed into
- **ARM_SUBSCRIPTION_ID** - The Azure subscription that is being deployed into