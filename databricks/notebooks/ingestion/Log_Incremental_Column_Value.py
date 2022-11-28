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
dbutils.widgets.text("file_name", "")
task_path = getArgument("task_path")
file_name = getArgument("file_name")

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
incremental_column = yml_config["source"]["incremental_column"]
incremental_column_data_type = yml_config["source"]["incremental_column_data_type"]
path = yml_config["target"]["file_path"]
if not path.endswith("/"):
    path += "/"
if "schema" in yml_config["target"]:
    schema = yml_config["target"]["schema"]
else:
    schema = None
if "file_type" in yml_config["target"]:
    file_type = yml_config["target"]["file_type"]
else:
    file_type = "parquet"
# Check if we are processing a single file or an entire directory
if file_name:
    path += file_name
file_path = f'abfss://{yml_config["target"]["storage_container_name"]}@{storage_account_dataLake}.dfs.core.windows.net/{path}'
try:
    # Get the latest value from the file. Use a schema for the data frame if needed
    if schema:
        df = spark.read.format(file_type).schema(schema).load(file_path)
    else:
        df = spark.read.format(file_type).load(file_path)
    if incremental_column_data_type.lower() == "datetime":
        latest_value = str(df.select(incremental_column).agg({incremental_column: "max"}).withColumnRenamed(f"max({incremental_column})", "incremental_value").selectExpr(f"date_format(incremental_value, 'YYYY-MM-dd HH:mm:ss.S')").collect()[0][0])
    else:
        latest_value = str(df.agg({incremental_column: "max"}).collect()[0][0])
    if latest_value is not None and latest_value != "None":
        # Write the latest value to the raw.incremental_load_log table
        write_incremental_load_log(source_system=yml_config["source"]["system_name"], object_name=yml_config["source"]["object_name"], incremental_column=incremental_column, file_name=file_name, incremental_value=latest_value)
    else:
        print(f"No data present in file {file_name}")
except Exception as exc:
    # Write the task log for the task failure
    write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Failed", error_message=str(exc))
    raise Exception(exc)
