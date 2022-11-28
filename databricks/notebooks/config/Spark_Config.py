# Databricks notebook source
# DBTITLE 1,Set the storage variables
storage_account_name = dbutils.secrets.get(scope='datalakeconfig', key='storageAccountDataLake')
storage_account_name_generic = dbutils.secrets.get(scope='datalakeconfig', key='storageAccountGeneric')
tenant_id = dbutils.secrets.get(scope='datalakeconfig', key='tenantID')

# COMMAND ----------

# DBTITLE 1,Set the storage config for the storage accounts
# Set the config for the data lake storage account
spark.conf.set("storageAccountDataLake", storage_account_name)
spark.conf.set("storageAccountGeneric", storage_account_name_generic)
spark.conf.set(f"fs.azure.account.auth.type.{storage_account_name}.dfs.core.windows.net", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account_name}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account_name}.dfs.core.windows.net", dbutils.secrets.get(scope='datalakeconfig', key='databricksApplicationID'))
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account_name}.dfs.core.windows.net", dbutils.secrets.get(scope='datalakeconfig', key='databricksApplicationKey'))
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account_name}.dfs.core.windows.net", f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")
# Set the config for the generic storage account
spark.conf.set(f"fs.azure.account.key.{storage_account_name_generic}.blob.core.windows.net", dbutils.secrets.get(scope='datalakeconfig', key='storageAccountGenericKey'))

# COMMAND ----------

# DBTITLE 1,Set the function app Spark config
spark.conf.set("functionAppBaseURL", dbutils.secrets.get(scope="datalakeconfig", key="functionAppBaseURL"))
spark.conf.set("functionAppFunctionKey", dbutils.secrets.get(scope="datalakeconfig", key="functionAppFunctionKey"))

# COMMAND ----------

# DBTITLE 1,Set the generic Spark config
spark.conf.set("spark.sql.broadcastTimeout", 3600)
spark.conf.set("spark.sql.legacy.timeParserPolicy", 'LEGACY')
