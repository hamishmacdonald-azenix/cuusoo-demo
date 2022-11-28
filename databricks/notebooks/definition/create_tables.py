# Databricks notebook source
# DBTITLE 1,Running Spark config
# MAGIC %run ../../notebooks/config/Spark_Config

# COMMAND ----------

# DBTITLE 1,Import the generic function
# MAGIC %run ../../notebooks/Functions_Collection

# COMMAND ----------

# DBTITLE 1,Create schemas
# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze;
# MAGIC CREATE SCHEMA IF NOT EXISTS silver;
# MAGIC CREATE SCHEMA IF NOT EXISTS gold;

# COMMAND ----------

# DBTITLE 1,Creating raw.incremental_load_log table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS bronze.incremental_load_log (
  log_pk bigint GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1),
  source_system string,
  incremental_column string,
  object_name string,
  file_name string,
  incremental_value string,
  ingestion_dtc timestamp
) 
USING DELTA
LOCATION "abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/bronze/incremental_load_log"
;
""")
