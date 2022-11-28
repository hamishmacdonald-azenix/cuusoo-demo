# Azure Data Factory

This folder contains all the Azure Data Factory (ADF) artefacts that are published to the service through the PowerShell script [Publish-DataFactory.ps1](Publish-DataFactory.ps1), which utilises the [azure.datafactory.tools](https://www.powershellgallery.com/packages/azure.datafactory.tools/0.17.0) PowerShell module. This can be run in your DevOps tool of choice. Ensure you have the latest version of [PowerShell 7](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.3) installed before attempting to run a deployment.

This PowerShell module uses configuration files to override various ADF settings at deployment time, based on the files contained in the [deployment](deployment) directory. Create a separate file for each environment you intend to deploy to using the convention `config-<Environment Name>.csv` and pass the `Environment Name` to the PowerShell script mentioned earlier in this article.

The high-level folder structure below outlines the structure of the ADF solution:

- [dataset](dataset) - All data sets
- [deployment](deployment) - All the `csv` configuration files used to set properties to be overridden at deployment time
- [integrationRuntime](integrationRuntime) - All the integration runtime definitions
- [linkedService](linkedService) - All the generic linked services
- [managedVirtualNetwork](managedVirtualNetwork) - The single managed virtual network resource
- [pipeline](pipeline) - All pipelines reposible for ingestion and orchestration

The current implementation of ADF deploys 2 Azure Integration Runtimes (IR):
- The out-of-the-box `AutoResolve` IR
- An Azure-hosted IR which integrated with the deployed [ADF managed virtual network](https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint), used to connect securely to other Azure services using managed private endpoints.

If you wish to deploy another self-hosted runtime, you can add the virtual machine deployment to the [Terraform project](infra/terraform) in this solution and create another IR definition in the `integrationRuntime` folder.