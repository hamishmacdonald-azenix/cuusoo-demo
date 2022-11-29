# Cuusoo Azure Ingestion Framework

HAMISH test blah blah blah

At its core, the framework uses an Azure function to orchestate Azure Data Factory (ADF) pipeline execution through YAML configuration files housed in an Azure storage account. The diagram below provides an overview of the process flow.

![Master ingestion flow](/documentation/Ingestion-Master%20Ingestion.png)

1. The YAML configuration files are read from a blob storage account
2. Secrets defined in the YAML configuration files are read from a deployed Azure Key Vault instance
3. The YAML configuration defined for the task is converted to json and passed into the ADF pipeline as a single parameter called `task_json`
4. The ADF pipeline is invoked by the Azure Function

The framework is built of on the premise of using Terraform to deploy all the Infrastructure as Code (IaC). The sections to follow will provide guidance around the deployment of the framework into a customer's environment.

The high-level folder structure below outlines the structure of the repo. The `README.md` file in each sub-folder will provide more information around the contents and usage of each section:

- [automation-config](automation-config) - Contains all the YAML-based configuration files that are used to drive ingestion and Databricks job execution
- [data-factory](data-factory) - Contains all the data factory artefacts
- [databricks](databricks) - Contains all the Databricks notebooks
- [databricks-config](databricks-config) - Contains all the configuration for the Databricks workspace deployments
- [documentation](documentation) - Contains all the project documentation
- [functions](functions) - Contains all the Azure function code
- [infra](infra) - Contains all the YAML configuration files, deployment scripts and terraform code for the infrastructure deployment
- [logic-apps](logic-apps) - Contains the source files and Bash scripts used to deploy either a consumption-based or Standard Workflow logic app

## Azure Prerequisites
In order to deploy into the customers Azure tenancy and related subscription/s, an app registration and service principal with `Contributor` and `User Access Administrator` RBAC role assignments on the relevant subscription (Resource Groups if subscription-level access is not an option) is required. 

If this principal should be able to create Azure Active Directory groups and maintain group members, additional delegated permissions to the `Microsoft Graph` API need to be provisioned and admin consent must be granted, including:

- Directory.Read.All
- Group.Create
- GroupMember.ReadWrite.All

Only the `Directory.Read.All` API permission is required if existing groups needs to be read.