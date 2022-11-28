# Databricks notebook source
# MAGIC %md
# MAGIC This notebook reads a yml configuration file from the data lake storage account in order to apply table properties and table optimisation tasks

# COMMAND ----------

# DBTITLE 1,Set the Spark config
# MAGIC %run ../../notebooks/config/Spark_Config

# COMMAND ----------

# DBTITLE 1,Import the generic functions
# MAGIC %run ../../notebooks/Functions_Collection

# COMMAND ----------

# DBTITLE 1,Remove all widgets - This is only to be used for testing purposes
# dbutils.widgets.removeAll()

# COMMAND ----------

# DBTITLE 1,Add widget for ADF parameter
dbutils.widgets.text("task_path", "")
task_path = getArgument("task_path")

# COMMAND ----------

# DBTITLE 1,Write the initial task log
write_task_log(task_path, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "Running")

# COMMAND ----------

# DBTITLE 1,Read the yaml config file from storage
storageAccountGeneric = spark.conf.get("storageAccountGeneric")
storageAccountDataLake = spark.conf.get("storageAccountDataLake")
configStorageURL = f"wasbs://config@{storageAccountGeneric}.blob.core.windows.net/{task_path}"
ymlConfig = read_yml_config(configStorageURL, f"/tmp/{task_path}")

# COMMAND ----------

# DBTITLE 1,Run the table maintenance tasks
# Declare a variable for caching as we need to send the output to another task job for execution
cache_table_list = []

def maintain_table(table: object):
    """
    Function to apply table properties, vacuum tables and optimise by z-ordering if required
    """
    # Adding table properties
    try:
        table_props = table["table_properties"]
        if table_props:
            exist_props = spark.sql(f'SHOW TBLPROPERTIES {table["table_name"]}').collect()
            properties = [req_prop for req_prop in table_props if req_prop["name"] not in [exist_prop["key"] for exist_prop in exist_props]]
            properties_values = [req_prop for req_prop in table_props for exist_prop in exist_props if req_prop["name"] == exist_prop["key"] and req_prop["value"] != exist_prop["value"]]
            # New properties
            if properties:
                for table_property in properties:
                    spark.sql(f'ALTER TABLE {table["table_name"]} SET TBLPROPERTIES({table_property["name"]} = "{table_property["value"]}")')
                    print(f'Adding property {table_property["name"]} with value "{table_property["value"]}" completed for table {table["table_name"]}')
            # Modified properties
            if properties_values:
                for table_property in properties_values:
                    spark.sql(f'ALTER TABLE {table["table_name"]} SET TBLPROPERTIES({table_property["name"]} = "{table_property["value"]}")')
                    print(f'Setting property {table_property["name"]} to "{table_property["value"]}" completed for table {table["table_name"]}')
    except Exception as exc:
        print(f'Setting table properties not required or failed for table {table["table_name"]}. {exc}')     
    # Vacuuming
    try:
        if table["vacuum_retention_hours"]:
            spark.sql(f'VACUUM {table["table_name"]} RETAIN {table["vacuum_retention_hours"]} HOURS')
            print(f'Vacuuming completed for table {table["table_name"]} with retention hours {table["vacuum_retention_hours"]}')
    except Exception as exc:
        print(f'Vacuuming not required or failed for table {table["table_name"]}. {exc}')
    # Calculating all column statistics
    try:
        if table["compute_statistics_all_columns"]:
            spark.sql(f'ANALYZE TABLE {table["table_name"]} COMPUTE STATISTICS FOR ALL COLUMNS')
            print(f'Computing all column statistics completed for table {table["table_name"]}')
    except Exception as exc:
        print(f'Computing all column statistics not required or failed for table {table["table_name"]}. {exc}')   
    # Z Ordering 
    try:
        if table["z_order_by"]:
            spark.sql(f'OPTIMIZE {table["table_name"]} ZORDER BY {table["z_order_by"]}')
            print(f'Z Ordering completed for table {table["table_name"]} on column/s {table["z_order_by"]}')
    except Exception as exc:
        print(f'Z Ordering not required or failed for table {table["table_name"]}. {exc}')
    # Caching
    try:
        if table["cache"]:
            cache_table_list.append(table["table_name"]) 
    except Exception:
        print(f'No caching required')
    
def process_tables():
    """
    Function to process all the tables in parallel
    """
    tables = ymlConfig["tables"]
    results = parallel_run(maintain_table, tables)
    results = [r for r in results]
    return results
    
try:
    process_tables()  
    # Write the task log for the completion of the task
    write_task_log(task_path, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "Completed")
    # Write the task variable if needed
    if cache_table_list:
        dbutils.jobs.taskValues.set(key = "cache_table_list", value = cache_table_list)
except Exception as exc:
    print(exc)
    # Write the task log for the task failure
    write_task_log(task_path, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "Failed", str(exc))
