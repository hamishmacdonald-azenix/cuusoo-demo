# Databricks notebook source
# MAGIC %md
# MAGIC This notebook reads a yml config file from the data lake storage account in order to read unprocessed files from the data lake, load the files into a delta table and finally move the files to a processed directory
# MAGIC 
# MAGIC All the required configuration is read from the yml file, the content of which is defined in [this](https://cogstate.atlassian.net/wiki/spaces/CDP/pages/1883439370/Data+Ingestion) Confluence document

# COMMAND ----------

# DBTITLE 1,Remove all widgets - This is only to be used for testing purposes
# dbutils.widgets.removeAll()

# COMMAND ----------

# DBTITLE 1,Add widget for ADF parameters
dbutils.widgets.text("task_path", "")
task_path = getArgument("task_path")

# COMMAND ----------

# DBTITLE 1,Set the Spark config
# MAGIC %run ../config/Spark_Config

# COMMAND ----------

# DBTITLE 1,Import the generic functions
# MAGIC %run ../Functions_Collection

# COMMAND ----------

# DBTITLE 1,Read the yaml config file from storage
storage_account_generic = spark.conf.get("storageAccountGeneric")
storage_account_dataLake = spark.conf.get("storageAccountDataLake")
config_storage_url = f"wasbs://config@{storage_account_generic}.blob.core.windows.net/{task_path}"
yml_config = read_yml_config(config_storage_url, f"/tmp/{task_path}")

# COMMAND ----------

# DBTITLE 1,Read and return the latest value for the incremental column
try:
    system_name = yml_config["source"]["system_name"]
    object_name = yml_config["source"]["object_name"]
    incremental_column = yml_config["source"]["incremental_column"]
    latest_value = spark.sql(f"SELECT MAX(incremental_value) FROM bronze.incremental_load_log WHERE source_system = '{system_name}' AND object_name = '{object_name}' AND incremental_column = '{incremental_column}'").collect()[0][0]
    if not latest_value:
        latest_value = ""
    dbutils.notebook.exit(str(latest_value))
except Exception as exc:
    # Write the task log for the task failure
    write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Failed", error_message=str(exc))
    raise Exception(exc)
