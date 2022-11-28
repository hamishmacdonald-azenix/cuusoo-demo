# Azure Functions

This folder contains the core code base deployed to an Azure function app contained within a dedicated Azure App Service Plan.

The high-level folder structure below outlines the functions that exist in the functions project:

- [get-keyvault-secret](functions/get-keyvault-secret/__init__.py) - Used to retrieve secrets from the deployed Key Vault instance
- [master-schedule-run](functions/master-schedule-run/__init__.py) - The master function which orchestrates the entire solution. The default timer trigger runs the function every 5 minutes - This can be adjusted in the [functions.json](functions/master-schedule-run/function.json) file, in the line of code below:
  
  ```json
  "schedule": "0 */5 * * * *"
  ```
- [read-task-log](functions/read-task-log/__init__.py) - Used to read the log file for a given task. A log file is written to the `Logs` path in the storage account where the YAML configuration files are housed
- [read-yaml-config](functions/read-yaml-config/__init__.py) - Used to read a YAML configuration file from storage and convert it into a `json` response, for use in the Azure Data Factory pipelines
- [sharepoint-file-download](functions/sharepoint-file-download/__init__.py) - The function used to download files from a SharePoint document library configured in SharePoint file ingestion tasks
- [write-task-log](functions/write-task-log/__init__.py) - Used to write a log file entry from a Databricks instance

All common function are contained in the [common.py](functions/common.py) file which is deployed to the function app as well.

Required libraries are defined in the [requirements.txt](functions/requirements.txt) file.

## Local development

To test your code locally, follow [this](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=csharp) guide provided by Microsoft, which involves installing the Azure Functions extension in VS Code

## Deployment

To deploy the function app to Azure, run the command below from the terminal, specifying the name of the Azure Function app that needs to be deployed to.

```
func azure functionapp publish <Azure Function App Name> --python
```