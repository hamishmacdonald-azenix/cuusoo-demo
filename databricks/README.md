# Databricks

This folder contains all the Databricks notebooks deployed as part of the ingestion framework.

All generic functions are contained in the [Functions_Collection.py](notebooks/Functions_Collection.py) Python file and imported into required notebooks using the `%run` command. 

The high-level folder structure below outlines the structure of the Databricks solution:

- [config](config) - A Spark configuration file which reads secrets from Azure Key Vault and writes them to the local Spark config. This will is imported into required notebooks using the `%run` command
- [definition](definition) - A file which contains the definitions for the bronze `incremental_load_log` table, as well as all tables created in the `silver` and `gold` layers of the data lakehouse
- [ingestion](ingestion) - Generic notebooks used to import data from the raw area of the lake into bronze delta tables
- [maintenance](maintenance) - Generic notebooks used to cache tables and apply generic delta table maintenance tasks, as defined in the [maintenance](automation-config/maintenance/table_maintenance_raw.yml) framework task
- [testing](testing) - All notebooks that can be used as a starting point for defining data quality and generic function tests.

## Deployment

The contents of this folder is made available within the Databricks service using the [Databricks repo integration](https://docs.databricks.com/repos/repos-setup.html) feature. You are required to manually create a folder for your repository in the respective Databricks workspaces and integrate with the repo you have created in the customer's environment using [this](https://docs.databricks.com/repos/get-access-tokens-from-git-provider.html) guide. 

Best practice is generally to limit the access to this repo as users are intended to create their own repo integration under the context of their own personal user account within Databricks. Consider using a branching strategy to ensure that each environment is update to date with the given branch. e.g. attach your development workspace to a `development` branch and your production workspace to the `main` or `production` branch.

Databricks has a repos API endpoint which you need to call to synchronise the files in the specified repo with the given branch. The [repo_refresh.py](repo_refresh.py) can be used to achieve this in your DevOps pipeline, once the environment variables below have been set:

- **token** - The generated Databricks PAT
- **databricks_url** - The URL to the Databricks workspace
- **repo_id** - This can be obtained from the URL when browsing the repo in the Databricks service
