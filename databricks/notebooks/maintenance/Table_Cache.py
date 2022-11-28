# Databricks notebook source
# MAGIC %md
# MAGIC This notebook is executed as part of the **Table-Caching** job and makes use of job task values <br>
# MAGIC https://docs.microsoft.com/en-gb/azure/databricks/dev-tools/databricks-utils#--taskvalues-subutility-dbutilsjobstaskvalues

# COMMAND ----------

# DBTITLE 1,Get the list of tables to cache
cache_table_list = dbutils.jobs.taskValues.get(taskKey = "Table-Cache-List-Get", key = "cache_table_list", default = [], debugValue = ["reporting.cognigram_order_details"])

# COMMAND ----------

# DBTITLE 1,Import the generic functions
# MAGIC %run ../../notebooks/Functions_Collection

# COMMAND ----------

# DBTITLE 1,Cache the tables
def cache_table(table_name: str):
    """
    Function to cache a table
    """
    try:
        spark.sql(f"CACHE TABLE {table_name}")
        print(f'Caching completed for table {table_name}')
    except Exception as exc:
        print(f'Caching failed for table {table_name}. {exc}')
        
def cache_tables():  
    """
    Function to cache all the tables in parallel
    """
    results = parallel_run(cache_table, cache_table_list)
    results = [r for r in results]
    return results

cache_tables()    
