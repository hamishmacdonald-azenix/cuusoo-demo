# Databricks notebook source
# MAGIC %md
# MAGIC This notebook reads a yml config file from the data lake storage account in order to read unprocessed files from the data lake, load the files into a delta table and finally move the files to a processed directory
# MAGIC 
# MAGIC All the required configuration is read from the yml file, the content of which is defined in [this](https://cogstate.atlassian.net/wiki/spaces/CDP/pages/1883439370/Data+Ingestion) Confluence document

# COMMAND ----------

# DBTITLE 1,Remove all widgets - This is only to be used for testing purposes
# dbutils.widgets.removeAll()

# COMMAND ----------

# DBTITLE 1,Add widget for ADF parameter
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
try:
    yml_config = read_yml_config(config_storage_url, f"/tmp/{task_path}")
except Exception as exc:
    print(f"Config file located at path {config_storage_url} does not exist or path is incorrect. Exiting notebook")
    raise Exception(exc) 

# COMMAND ----------

# DBTITLE 1,Write the initial task log
write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Running")

# COMMAND ----------

# DBTITLE 1,Load the data into the target raw table
# Get all the values from the config file
file_format = yml_config.get("source").get("file_format")
delimiters = yml_config.get("source").get("delimiters")
schema = yml_config.get("source").get("schema")
file_name_search = yml_config.get("source").get("file_name_search")
key_columns = yml_config.get("target").get("key_column_list")
target_table_name = yml_config.get("target").get("delta_table_name")
load_type = yml_config.get("target").get("load_type")
file_path = f'abfss://{yml_config["source"]["storage_container_name"]}@{storage_account_dataLake}.dfs.core.windows.net/{yml_config["source"]["file_path"]}'
run_date = datetime.now().strftime("%Y/%m/%d")
# Check if there are files to process
try:
    dbutils.fs.ls(file_path)
    # Exit if the path exists but there are no files
    if not file_path:
        # Write the task log for the completion of the task
        write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Completed")
        # Exit the notebook
        dbutils.notebook.exit("No files available to process")
except:
    # Write the task log for the completion of the task
    write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Completed")
    # Exit the notebook
    dbutils.notebook.exit("No files available to process")
try:
    if file_name_search:
        file_list = [file for file in dbutils.fs.ls(file_path) if file.name.lower().startswith(file_name_search.lower())]
    else:
        file_list = [file for file in dbutils.fs.ls(file_path)]
    for file in file_list:
        source_file_path = file.path
        # Check if we need to append a date stamp to the file_name before loading it
        append_date_to_filename = yml_config.get("target").get("append_date_to_filename")
        if append_date_to_filename:
            file_name = source_file_path.split("/")[-1].split(".")[0] + "_" + datetime.utcnow().strftime("%Y%m%d") + "." + source_file_path.split("/")[-1].split(".")[-1]
            processed_file_name = source_file_path.replace("unprocessed", "processed").replace("Unprocessed", "Processed").replace(source_file_path.split("/")[-1], "") + "/" + run_date + "/" + file_name
        else:
            file_name = source_file_path.split("/")[-1]
            processed_file_name = source_file_path.replace("unprocessed", "processed").replace("Unprocessed", "Processed").replace(file_name, "") + run_date + "/" + file_name
        print(f"Start processing file {file_name}")
        # Read the file into a dataframe, depending on the file type
        dbfs_file_path = f'/tmp/{target_table_name.replace(".", "_")}/{source_file_path.split("/")[-1].split(".")[0]}/{source_file_path.split("/")[-1]}'
        df = spark.createDataFrame([], StructType([]))
        try:
            if file_format.lower() == "sas7bdat" and source_file_path.split(".")[-1].lower() == file_format.lower() :
                df = convert_sas_to_dataframe(file_path=source_file_path, dbfs_path=dbfs_file_path)
            elif file_format.lower() == "xlsx" and source_file_path.split(".")[-1].lower() == file_format.lower():
                df = convert_xlsx_to_dataframe(file_path=source_file_path, dbfs_path=dbfs_file_path)
            elif file_format.lower() in ["csv", "txt"] and source_file_path.split(".")[-1].lower() == file_format.lower():
                # Try each delimiter to see which one is being used
                for delimiter in delimiters:
                    df = convert_csv_to_dataframe(file_path=source_file_path, delimiter=delimiter)
                    if len(df.columns) > 1:
                        break
            elif file_format.lower() == "parquet" and source_file_path.split(".")[-1].lower() == file_format.lower():
                df = spark.read.parquet(source_file_path)
                for col in df.columns:
                    new_col = replace_invalid_chars(col)
                    df = df.withColumnRenamed(col, new_col)
            elif file_format.lower() == "json" and source_file_path.split(".")[-1].lower() == file_format.lower():
                if schema:
                    df = spark.read.format("json").schema(schema).load(source_file_path)
                else:
                    df = spark.read.json(source_file_path)
                for col in df.columns:
                    new_col = replace_invalid_chars(col)
                    df = df.withColumnRenamed(col, new_col)
        except Exception as exc:
            raise Exception(f"Unable to ingestion file {source_file_path}, Error Message: {str(exc)}") 
        if df.columns:
            # Check if we are loading a single file. If we are, use the file name as part of the delta table path
            base_file_path = source_file_path.split("unprocessed")[0].replace("raw", "bronze")
            if "." in yml_config["source"]["file_path"]:
                table_file_path = base_file_path + source_file_path.split("/")[-1].split(".")[0]
            elif file_name_search:
                table_file_path = base_file_path + file_name_search[0:-1]
            else:
                table_file_path = base_file_path
            # Create the temp table for the data load
            temp_table_name = f'tmp_{target_table_name.replace(".", "")}'
            # Add metadata columns to the dataframe
            df = df \
                .withColumn("raw_pk", F.lit(get_uuid()).cast("string")) \
                .withColumn("raw_filename", F.lit(file_name).cast("string")) \
                .withColumn("raw_fileloaddate", F.lit(get_filename_load_date(file_name)).cast("string")) \
                .withColumn("raw_ingestiondtc", F.lit(datetime.utcnow()).cast("timestamp")) \
                .withColumn("raw_updatedtc", F.lit(None).cast("timestamp")) \
                .withColumn("raw_changestatus", F.lit("I").cast("string"))
            create_column_list = ",".join([column[0] + " " + column[1] for column in df.dtypes])
            select_column_list = []
            df.createOrReplaceTempView(temp_table_name)
            # Check if the target table exists. Create it if it doesn't
            try:
                df_schema = spark.table(target_table_name).schema.fieldNames()
            except:
                spark.sql(f'CREATE TABLE {target_table_name}({create_column_list}) USING DELTA LOCATION "{table_file_path}"')
                if load_type.lower() == "full":
                    # Alter the table for delta retention to 1 day as we are creating a snapshot for every file
                    spark.sql(f"ALTER TABLE {target_table_name} SET TBLPROPERTIES(delta.logRetentionDuration='interval 1 days', delta.deletedFileRetentionDuration = 'interval 1 days',delta.autoOptimize.autoCompact = true)")
                df_schema = spark.table(target_table_name).schema.fieldNames()
            # Add new columns that have come in that are not in the target table
            table_column_list = [tableColumn for tableColumn in df_schema]
            dataset_column_list = [dfColumn for dfColumn in df.dtypes]
            for alter_table_sql in [f"ALTER TABLE {target_table_name} ADD COLUMN {dfColumn[0]} {dfColumn[1]}" for dfColumn in dataset_column_list if dfColumn[0] not in table_column_list]:
                spark.sql(alter_table_sql)
            # If it is a full load, remove the data for the new file and insert it. If it is incremental, use the generic merge
            if load_type.lower() == "incremental":
                cols_to_update = [("raw_filename", f"'{file_name}'"), ("raw_fileloaddate", f"'{get_filename_load_date(file_name)}'"), ("raw_updatedtc", "current_timestamp()"), ("raw_changestatus", "'U'")]
                key_column_list = [column for column in key_columns.split(",")]
                additional_cols_to_insert = [("raw_filename", f"'{file_name}'"), ("raw_fileloaddate", f"'{get_filename_load_date(file_name)}'"), ("RAW_INGESTIONDTC", "current_timestamp()"),  ("raw_changestatus", "'I'")]
                generic_table_merge(source_data_frame=df, target_table=target_table_name, join_column_list=key_column_list, update_add_columns=cols_to_update, insert_add_columns=additional_cols_to_insert, add_missing_columns=True)
            elif load_type.lower() == "full":
                # Remove the data for the current file if it exists
                spark.sql(f"DELETE FROM {target_table_name} WHERE raw_filename = '{file_name}'")
                # Get the full list of columns to insert
                df_schema = spark.table(target_table_name).schema.fieldNames()
                table_column_list = [tableColumn for tableColumn in df_schema]
                dataset_column_list = [dfColumn[0] for dfColumn in df.dtypes]
                select_column_list = ",".join(["`" + column + "`" if column in dataset_column_list else f"null AS `{column}`" for column in table_column_list])
                insert_column_list = ",".join(["`" + column + "`" for column in table_column_list])
                # Insert the data
                spark.sql(f"INSERT INTO {target_table_name}({insert_column_list}) SELECT {select_column_list} FROM {temp_table_name}")
            # Move the file to the processed directory
            dbutils.fs.mv(source_file_path, processed_file_name)
            print(f"Successfully processed file {file_name}")
        elif df.columns == [] and source_file_path.split(".")[-1].lower() == file_format.lower():
            # Move the file to the processed directory
            dbutils.fs.mv(source_file_path, processed_file_name)
            print(f"File {file_name} does not contain any data - Marked as processed")
        else:
            print(f"File {file_name} not processed")
    # Write the task log for the completion of the task
    write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Completed")
except Exception as exc:
    # Write the task log for the task failure
    write_task_log(task_path=task_path, run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), run_status="Failed", error_message=str(exc))
    raise Exception(exc) 
