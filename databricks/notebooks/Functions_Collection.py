# Databricks notebook source
# DBTITLE 1,Import the required libraries
import os
import uuid
import requests
import re
from operator import add
from datetime import datetime
from functools import reduce
import pyspark.sql.functions as F
from pyspark.sql.types import StringType, TimestampType, StructType, StructField
from pyspark.sql import DataFrame
import yaml
from yaml import Loader
from sas7bdat import SAS7BDAT
import pandas as pd
from pyspark.sql.window import Window
import concurrent.futures

# COMMAND ----------

def replace_invalid_chars(string_value):
    """
    Replaces invalid characters that show up in the column names or anywhere really.
    """
    for char in "[,;{}()\n\t=]+'().-?":
        string_value = string_value.replace(char, '')
    for char in "/ ":
        string_value = string_value.replace(char, '_')
    return string_value

# COMMAND ----------

def convert_sas_to_dataframe(file_path, dbfs_path):
    """
    Reads a SAS file and returns a spark dataframe with the contents of the file.
    """
    fileName = dbfs_path.split("/")[-1]
    folderPath = dbfs_path.replace(fileName, "")[0:-1]
    if os.path.exists(dbfs_path):
        dbutils.fs.rm(folderPath, recurse=True)
    dbutils.fs.cp(file_path, f"{folderPath}/{fileName}")
    with SAS7BDAT(f"/dbfs{dbfs_path}", skip_header=False) as reader:
        pandas_df = reader.to_data_frame()
        if pandas_df.empty:
            spark_df = spark.createDataFrame([], StructType([]))
        else:
            spark_df = spark.createDataFrame(pandas_df.astype(str))
    dbutils.fs.rm(folderPath, recurse=True)
    for col in spark_df.columns:
        new_col = replace_invalid_chars(col.upper())
        spark_df = spark_df.withColumnRenamed(col, new_col)
    return spark_df

# COMMAND ----------

def convert_xlsx_to_dataframe(file_path, dbfs_path):
    """
    Reads a xlsx file and returns a spark dataframe with the contents of the file.
    """
    fileName = dbfs_path.split("/")[-1]
    folderPath = dbfs_path.replace(fileName, "")[0:-1]
    if os.path.exists(dbfs_path):
        dbutils.fs.rm(folderPath, recurse=True)
    dbutils.fs.cp(file_path, f"{folderPath}/{fileName}")
    df = pd.read_excel(f"/dbfs{dbfs_path}", index_col=None, engine='openpyxl')
    dbutils.fs.rm(folderPath, recurse=True)
    spark_df = spark.createDataFrame(df.astype(str))
    for col in spark_df.columns:
        new_col = replace_invalid_chars(col.upper())
        spark_df = spark_df.withColumnRenamed(col, new_col)
    return spark_df

# COMMAND ----------

def convert_csv_to_dataframe(file_path, delimiter=","):
    """
    Reads a csv file and returns a spark dataframe with the contents of the file.
    """
    spark_df = spark.read.option('header', True).option("delimiter", delimiter).csv(file_path)
    for col in spark_df.columns:
        new_col = replace_invalid_chars(col.upper())
        spark_df = spark_df.withColumnRenamed(col, new_col)
    return spark_df

# COMMAND ----------

def read_yml_config(file_path, dbfs_path):
    """
    Read a yaml config file from the given storage path and return the contents
    """
    dbutils.fs.cp(file_path, dbfs_path)
    ymlConfig = yaml.load(open("/dbfs" + dbfs_path, "r"), Loader=Loader)
    dbutils.fs.rm(dbfs_path)
    return ymlConfig

# COMMAND ----------

def drop_database_tables(database):
    """
    Drops all tables in a given databse. Use with care! Written for new/dev setups mostly.
    """
    tables_list = spark.catalog.listTables(database)
    for table in tables_list:
        try:
            print (f'Dropping table: {table.name}')
            spark.sql(f'DROP TABLE {database}.{table.name}')
        except Exception as e:
            print (f'Error occurred when trying to drop table {database}.{table.name}: {e}')

# COMMAND ----------

def delete_delta_folder(database_name: str, table_name: str) -> None:
    """Deletes delta folder corresponding to the given table details."""
    print (f"Deleting abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/{database_name.title()}/{table_name}")
    dbutils.fs.rm(f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/{database_name.title()}/{table_name}", True)

# COMMAND ----------

def delete_datalake_layer(datalake_layer: str) -> None:
    """Deletes all folders available in a datalake layer provided."""
    for table in spark.catalog.listTables(datalake_layer):
            delete_delta_folder(datalake_layer, table.name)

# COMMAND ----------

get_uuid = udf(lambda : str(uuid.uuid4()), StringType())
# UDF to generate a standard UUID4. Used mostly for primary key generation.

# COMMAND ----------

def dataframe_table_column_sync(given_dataframe, table_name):
    """
    Drops unexpected columns from a given dataframe (columns not present in the table given). Adds expected columns if not available in the given dataframe (null values added). Returns the modified dataframe.
    """
    table_cols = spark.sql(f'SELECT * FROM {table_name} LIMIT 1').columns
    for col in given_dataframe.columns:
        if col not in table_cols:
            print (f'Unexpected column {col} dropped from the new data.')
            given_dataframe = given_dataframe.drop(col)
    for col in table_cols:
        if col not in given_dataframe.columns and col not in ['CHANGESTATUS', 'INGESTIONDTC', 'UPDATEDTC']:   #these columns are dynamically added by merge function
            print (f'Column {col} was missing from the new data. Column now added with null values.')
            given_dataframe = given_dataframe.withColumn(col, F.lit(None))
    return given_dataframe

# COMMAND ----------

def write_task_log(task_path, run_date, run_status, error_message=None):
    """
    Used to write the task log progress to the blob store for the given task by calling the write-task-log Azure function
    """
    functionAppBaseURL = spark.conf.get("functionAppBaseURL")
    if "/" != functionAppBaseURL[-1]:
        functionAppBaseURL + "/"
        functionAppURL = functionAppBaseURL + "/api/write-task-log"

    headers={
        'x-functions-key': spark.conf.get("functionAppFunctionKey")
    }
    data = {
        'task_path' : task_path,
        'run_date' : run_date,
        'run_status' : run_status,
        'error_message' : error_message
    }
    requests.post(url=functionAppURL, headers=headers, json=data)

# COMMAND ----------

def with_summed_rows_ignoring_nulls(df : DataFrame, new_col : str, col_list : list) -> DataFrame:
    """
    Sums the values in the given column list and returns a new dataframe with a new column with the sum value. If one or more null values are present in the given columns, they are treated as 0.
    """
    return df.withColumn(new_col, reduce(add, [F.coalesce(F.col(x), F.lit(0)) for x in col_list]))


# COMMAND ----------

def with_summed_rows(df : DataFrame, new_col : str, col_list : list) -> DataFrame:
    """
    Sums the values in the given column list and returns a new dataframe with a new column with the sum value. If one or more null values are present in the given columns, the sum will also be a null.
    """
    return df.withColumn(new_col, reduce(add, [F.col(x) for x in col_list]))


# COMMAND ----------

def get_transposed_qs(formnm_filter:str) -> DataFrame:
    """
    Returns a transposed dataframe from a subset of main_qs and result_base tables. To be used in results notebooks
    """
    df = spark.sql(f"""
    SELECT
      uform_pk
      ,internal_study_name
      ,general_research_access
      ,active_study
      ,QSTEST AS qs_test
      ,QSORRES AS qs_orres
    FROM
      (
      SELECT
        rb.uform_pk
        ,rb.internal_study_name
        ,rb.internal_study_name
        ,rb.general_research_access
        ,rb.active_study
        ,mqs.QSTEST
        ,mqs.QSORRES
        ,ROW_NUMBER() OVER(PARTITION BY rb.uform_pk, mqs.QSTEST ORDER BY rb.update_dtc DESC) AS row_id
      FROM
        curated.result_scale_base rb
        INNER JOIN transformed.main_qs mqs ON rb.study_name = mqs.STDYNM 
            AND rb.site_number = mqs.SITENUM
            AND rb.screening_number = mqs.SCRNUM
            AND rb.visit_name = mqs.VISITNM
            AND rb.form_name = mqs.FORMNM
      WHERE
        mqs.FORMNM LIKE '%{formnm_filter}%'
      ) rb
    WHERE
      rb.row_id = 1
    """)
    
    grouped_df = df.groupBy('uform_pk', 'internal_study_name', 'general_research_access', 'active_study').pivot('qs_test').agg(F.first('qs_orres'))

    for col in grouped_df.columns:
        updated_col = replace_invalid_chars(col.lower())
        grouped_df = grouped_df.withColumnRenamed(col, updated_col)
    
    return grouped_df

# COMMAND ----------

def generic_table_merge(source_data_frame:DataFrame, target_table:str, join_column_list:list, update_add_columns:list=[], insert_add_columns:list=[], add_missing_columns:bool=False, ignore_for_match_columns:list=[], generated_columns:list=[]) -> DataFrame:
    """
    This function :
    * will merge results into a target table given a source data frame and a join column list. 
    * allows for the user to explicitly set some columns and their values to be inserted/added.
    * allows for the user to auto generate columns if they're missing at the target table.
    * allows for the user to ignore column(s) when checking for match condition
    """
    # Create a temporary table for the MERGE source
    sourceTable = "tmp_" + target_table.replace(".", "_")
    source_data_frame.createOrReplaceTempView(sourceTable)
    filePath = target_table.split(".")[0].title() + "/" + target_table.split(".")[-1].lower()
    tableLocation = f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/{filePath}"
    # Get all the source data frame columns without any key columns
    dataframeColumnList = [column for column in source_data_frame.dtypes if column[0] not in join_column_list and column[0] not in ignore_for_match_columns]
    # Create the target table if it doesn't exist
    try:
        tableExists = True
        targetSchema = spark.table(target_table).schema.fieldNames()
    except:
        tableExists=False
        createColumnList = ",".join([column[0] + " " + column[1] for column in source_data_frame.dtypes])
        spark.sql(f'CREATE TABLE {target_table}({createColumnList}) USING DELTA LOCATION "{tableLocation}"')
    if tableExists == True:
        if add_missing_columns == True:
            # Add new columns that have come in that are not in the target table
            tableColumnList = [tableColumn for tableColumn in targetSchema]
            for alterTableSQL in [f"ALTER TABLE {target_table} ADD COLUMN {dfColumn[0]} {dfColumn[1]}" for dfColumn in dataframeColumnList if dfColumn[0] not in tableColumnList]:
                spark.sql(alterTableSQL)
    # Get all the columns for the insert
    insertColumnList = [column for column in spark.table(target_table).dtypes if column[0] not in [column[0] for column in update_add_columns] and column[0] not in generated_columns]
    # Get all the columns for the update
    updateColumnList = [column for column in spark.table(target_table).dtypes if column[0] not in [column[0] for column in update_add_columns] and column[0] not in [column[0] for column in insert_add_columns] and column[0] not in join_column_list and column[0] not in ignore_for_match_columns and column[0] not in generated_columns]
    # Get all the column sets needed for the MERGE operation
    joinColumns = " AND ".join([f"S.{column} = T.{column}" for column in join_column_list])
    # Determine what values to use for IfNull based on the data types
    numericArray = ["short", "long", "decimal", "decimal(38,18)", "double", "int", "float"]
    updateColumnsNumeric = " OR ".join([f"ifNull(CAST(S.{column[0]} AS {column[1]}), 0) <> ifNull(T.{column[0]}, 0)" for column in updateColumnList if column[1] in numericArray])
    updateColumnsNonNumeric = " OR ".join([f"ifNull(S.{column[0]}, '') <> ifNull(T.{column[0]}, '')" for column in updateColumnList if column[1] not in numericArray and column[1] not in ["binary", "boolean"]])
    updateColumnsBinary = " OR ".join([f"ifNull(S.{column[0]}, CAST('' AS BINARY)) <> ifNull(T.{column[0]}, CAST('' AS BINARY))" for column in updateColumnList if column[1] == "binary"])
    updateColumnsBoolean = " OR ".join([f"ifNull(S.{column[0]}, CAST(0 AS BOOLEAN)) <> ifNull(T.{column[0]}, CAST(0 AS BOOLEAN))" for column in updateColumnList if column[1] == "boolean"])
    updateColumnsCheck = " OR ".join(filter(None, [updateColumnsNumeric, updateColumnsNonNumeric, updateColumnsBinary, updateColumnsBoolean]))
    
    updateColumns = ",".join([f"T.{column[0]} = S.{column[0]}" for column in updateColumnList])
    # Add additional static update columns if required
    if update_add_columns != []:
        for updateCol in update_add_columns:
            updateColumns += "," + ",".join([f"T.{updateCol[0]} = {updateCol[1]}"])
    
    insertColumns = ",".join([column[0] for column in insertColumnList if column[0] not in [column[0] for column in insert_add_columns]])
    insertColumnValues = ",".join([f"S.{column[0]}" for column in insertColumnList if column[0] not in [column[0] for column in insert_add_columns]])
    if insert_add_columns != []:
        for insert_add_col in [column for column in insert_add_columns if column[0] not in insertColumnList and column[0] not in ignore_for_match_columns]:
            insertColumns += "," + ",".join({insert_add_col[0]})
            insertColumnValues += "," + ",".join({insert_add_col[1]})
               
    # Build up the final MERGE
    mergeStatement = f"""
    MERGE INTO {target_table} T 
    USING {sourceTable} S ON {joinColumns}
    WHEN MATCHED AND ({updateColumnsCheck})
    THEN UPDATE SET {updateColumns}
    WHEN NOT MATCHED THEN INSERT({insertColumns})
    VALUES ({insertColumnValues})
    """
#     print (mergeStatement)
    # Get the results of the MERGE
    result = spark.sql(mergeStatement).show()
#     result = mergeStatement
    # Drop the temp table
    spark.sql(f"DROP TABLE IF EXISTS {sourceTable}")
    return result


# COMMAND ----------

def get_valid_study(study_name: str, standard_studies: list, studies_map:dict) -> str:
    """
    This function will check if the given study_name has corresponding 'standard' study_name in the lookup table. If not, the given study_name is returned and       assumed to be correct value.
    """
    try:
        if study_name in studies_map.keys():
            return studies_map[study_name]
        else:
            return study_name
    except Exception as e:
        return f'error occurred: {e}'

# COMMAND ----------

def get_filename_load_date(file_name:str) -> str:
    """
    Splits a file name and returns the date stamp portion of the file name
    """
    if "_" in file_name.replace("-", "_").replace(".", "_"):
        file_name = [name for name in file_name.replace("-", "_").replace(".", "_").replace(" ", "").split("_") if len(name) >= 7 and name[0:2] == "20"]
    else:
        file_name = []
    if file_name != []:
        return file_name[0]
    else:
        return ""
                 
spark.udf.register("get_filename_load_date", get_filename_load_date)

# COMMAND ----------

def impose_table_schema_dataframe(target_table:str, new_df:DataFrame) -> DataFrame:
    """
    Imposes schema of an existing table(table with well defined schema)
    """
    df_tmp_cols = [colmn.lower() for colmn in new_df.columns]
    for col_dtls in spark.table(target_table).dtypes:
        col_name, dtype = col_dtls
        if col_name.lower() in df_tmp_cols:
            new_df = new_df.withColumn(col_name,F.col(col_name).cast(dtype))
        else:
            new_df = new_df.withColumn(col_name,F.lit(None).cast(dtype)) 
    return new_df

# COMMAND ----------

def add_table_column(table_name: str, column_name: str, data_type: str="string", comment: str=None, location: list=None) -> str:
    """
    This function will check if a column exists in a given table and will add it if it doesn't
    The location should be specified with 2 attributes, namely 'location' and 'column_name'
    https://docs.databricks.com/spark/latest/spark-sql/language-manual/sql-ref-syntax-ddl-alter-table.html
    """
    try:
        if column_name not in [column[0] for column in spark.table(table_name).dtypes]:
            alter_table = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}"
            if comment is not None:
                alter_table += f" COMMENT '{comment}'"
            if location is not None:
                alter_table += f" {location['location']} {location['column_name']}"
            spark.sql(alter_table)
            return f"Successfully added column {column_name} to table {table_name}"
        else:
            return f"Column {column_name} already exists in table {table_name}"
    except Exception as e:
        return f'error occurred: {e}'

# COMMAND ----------

def write_incremental_load_log(source_system: str, object_name: str, incremental_column: str, file_name: str, incremental_value: str) -> str:
    """
    This function will write a row to the raw.incremental_load_log table
    """
    spark.sql(f"""
    INSERT INTO bronze.incremental_load_log
    (
      source_system
      ,object_name
      ,incremental_column
      ,file_name
      ,incremental_value
      ,ingestion_dtc
    )
    SELECT
      '{source_system}'
      ,'{object_name}'
      ,'{incremental_column}'
      ,'{file_name}'
      ,'{incremental_value}'
      ,current_timestamp()
    """)

# COMMAND ----------

def write_reporting_table(table_name: str, sql_statement: str) -> None:
    """
    This function will take an input SQL command and use it to create a new or overwrite an existing reporting table
    """
    # Read the sql statement into a temp table
    df = spark.sql(sql_statement)
    tempTableName = "tmp_" + table_name.split(".")[-1]
    tableBaseName = table_name.split(".")[-1]
    df.createOrReplaceTempView(tempTableName)
    try:
        # Check if the table exists
        spark.table(table_name)
        print(f"Overwriting table {table_name}")
        spark.read.table(tempTableName) \
            .write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)
        print(f"Vacuum table {table_name}")
        spark.sql(f"VACUUM {table_name} RETAIN 720 HOURS")
        spark.catalog.dropTempView(tempTableName)
    except:
        print(f"Creating table {table_name}")
        spark.sql(f"""
        CREATE TABLE {table_name}
        USING DELTA
        LOCATION "abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/Reporting/{tableBaseName}/"
        AS
        SELECT * FROM {tempTableName}
        """)
        print(f"Set table properties for {table_name}")
        spark.sql(f"""
        ALTER TABLE {table_name} 
        SET TBLPROPERTIES(
            delta.autoOptimize.autoCompact = true
            ,delta.tuneFileSizesForRewrites = true
        )
        """)

# COMMAND ----------

def camel_to_snake_case(name: str) -> str:
    """
    Takes a camelCaseString and converts it to snake_case. Mostly used for renaming of the column names.
    """
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

# COMMAND ----------

def healthcare_raw_to_transformed_df(source_table: str, cols_to_rename: dict = {}, drop_temporal_columns: bool = True):
    """
    Reads data from a raw source_table and readies it for injection to transformed table.
    """
    # Identify if the data source is nouknow or cognigram

    product_name = source_table.split('.')[1].split('_')[0]
    df = (
        spark.table(source_table)
        .withColumnRenamed('RAW_PK', 'raw_table_id')
        .withColumn('HEALTHCARE_PRODUCT_NAME', F.lit(f'{product_name}'))
        .drop('RAW_UPDATEDTC', 'RAW_CHANGESTATUS', 'RAW_INGESTIONDTC', 'RAW_FILELOADDATE', 'RAW_FILENAME', 'RAW_RAW_FILELOADDATE')
         )
    # Drop any 'temporal' columns if existing
    if drop_temporal_columns:
        for column in df.columns:
            if 'Temporal' in column:
                print (f'Dropping temporal column : {column}')
                df = df.drop(column)
            
    # Convert all columns to lower_snake_case
    current_cols = df.columns
    new_cols = [camel_to_snake_case(col_name) for col_name in current_cols]
    renamed_df = df.toDF(*new_cols)
    
#     Apply necessary renames
    if cols_to_rename:
        for old_col, new_col in cols_to_rename.items():
            renamed_df = renamed_df.withColumnRenamed(old_col, new_col) if old_col in renamed_df.columns else renamed_df
            
    return renamed_df

# COMMAND ----------

def load_cognigram_nouknow_table(target_table: str, cognigram_source_table: str = None, nouknow_source_table: str = None, cols_to_rename: dict = {}, add_cols: list = [], join_cols: list = [], drop_temporal_columns : bool = True) -> None:
    """
    Reads a source table as a dataframe and injects the dataframe into target table.
    """
        
    # Generate cognigram and nouknow dataframe from raw tables where possible
    cognigram_df = healthcare_raw_to_transformed_df(cognigram_source_table, cols_to_rename, drop_temporal_columns) if cognigram_source_table else None
    nouknow_df = healthcare_raw_to_transformed_df(nouknow_source_table, cols_to_rename, drop_temporal_columns) if nouknow_source_table else None
   
    if cognigram_df and nouknow_df:
        df = cognigram_df.unionByName(nouknow_df, allowMissingColumns=True)
    elif nouknow_df:
        df = nouknow_df
    elif cognigram_df:
        df = cognigram_df
    else:
        raise ValueError ("No valid source tables were provided.")
        
   # Add columns required by target_table
    add_cols = set(spark.table(target_table).columns) - set(df.columns) - set(['update_dtc', 'ingestion_dtc', 'change_status'])
    if add_cols:
        for column in add_cols:
            df = df.withColumn(column, F.lit(None))
            
    # Merge the renamed_df into the target table
    cols_to_update = [("update_dtc", "current_timestamp()"), ("change_status", "'U'")]
    additional_cols_to_insert = [("ingestion_dtc", "current_timestamp()"), ("change_status", "'I'") ]

    # Check if there is a list of key columns specified
    if not join_cols:
        join_cols = ['id', 'healthcare_product_name']

    generic_table_merge(source_data_frame=df, target_table=target_table, join_column_list=join_cols, update_add_columns=cols_to_update, insert_add_columns=additional_cols_to_insert, add_missing_columns=False, ignore_for_match_columns=[])
    
    # Delete any non relevant data in target table
    df.createOrReplaceTempView('tmp_renamed_df')
    spark.sql(f"""
                DELETE FROM
                  {target_table} a
                WHERE
                    NOT EXISTS (
                        SELECT
                            id, healthcare_product_name
                        FROM
                            tmp_renamed_df b
                        WHERE
                            a.id = b.id
                        AND
                            a.healthcare_product_name = b.healthcare_product_name
                    )
                """).show()

# COMMAND ----------

def carp_raw_to_transformed_df(source_table: str, cols_to_rename: dict = {}):
    """
    Reads data from a raw source_table and readies it for injection to transformed table.
    """

    df = (
        spark.table(source_table)
        .withColumnRenamed('RAW_PK', 'raw_table_id')
        .drop('RAW_UPDATEDTC', 'RAW_CHANGESTATUS', 'RAW_INGESTIONDTC', 'RAW_FILELOADDATE', 'RAW_FILENAME')
         )
    # Drop any 'temporal' columns if existing
    for column in df.columns:
        if 'Temporal' in column:
            print (f'Dropping temporal column : {column}')
            df = df.drop(column)
            
    # Convert all columns to lower_snake_case
    current_cols = df.columns
    new_cols = [camel_to_snake_case(col_name) for col_name in current_cols]
    renamed_df = df.toDF(*new_cols)
    
#     Apply necessary renames
    if cols_to_rename:
        for old_col, new_col in cols_to_rename.items():
            renamed_df = renamed_df.withColumnRenamed(old_col, new_col) if old_col in renamed_df.columns else renamed_df
            
    return renamed_df


# COMMAND ----------

def ct_raw_to_transformed_df(source_table: str, cols_to_rename: dict = {}):
    """
    Reads data from a raw source_table and readies it for injection to transformed table.
    """

    df = (
        spark.table(source_table)
        .withColumnRenamed('RAW_PK', 'raw_table_id')
        .drop('RAW_UPDATEDTC', 'RAW_CHANGESTATUS', 'RAW_INGESTIONDTC', 'RAW_FILELOADDATE', 'RAW_FILENAME')
         )
    # Drop any 'temporal' columns if existing
    for column in df.columns:
        if 'Temporal' in column:
            print (f'Dropping temporal column : {column}')
            df = df.drop(column)
            
    # Convert all columns to lower_snake_case
    current_cols = df.columns
    new_cols = [camel_to_snake_case(col_name) for col_name in current_cols]
    renamed_df = df.toDF(*new_cols)
    
#     Apply necessary renames
    if cols_to_rename:
        for old_col, new_col in cols_to_rename.items():
            renamed_df = renamed_df.withColumnRenamed(old_col, new_col) if old_col in renamed_df.columns else renamed_df
            
    return renamed_df


def ct_transformed_table_load(target_table: str, source_table: str = None, cols_to_rename: dict = {}, add_cols: list = []) -> None:
    """
    Reads a source table as a dataframe and injects the dataframe into target table.
    """
    
   # Generate transformed layer consistent dataframe from source_table
    df = ct_raw_to_transformed_df(source_table, cols_to_rename)
   
        
       # Add columns required by target_table
    add_cols = set(spark.table(target_table).columns) - set(df.columns) - set(['update_dtc', 'ingestion_dtc', 'change_status'])
    if add_cols:
        for column in add_cols:
            df = df.withColumn(column, F.lit(None))
            
    # Merge the renamed_df into the target table
    cols_to_update = [("update_dtc", "current_timestamp()"), ("change_status", "'U'")]
    additional_cols_to_insert = [("ingestion_dtc", "current_timestamp()"), ("change_status", "'I'") ]


    generic_table_merge(source_data_frame=df, target_table=target_table, join_column_list=['id'], update_add_columns=cols_to_update, insert_add_columns=additional_cols_to_insert, add_missing_columns=False, ignore_for_match_columns=[])
    
    # Delete any non relevant data in target table
    df.createOrReplaceTempView('tmp_renamed_df')
    spark.sql(f"""
                DELETE FROM
                  {target_table} a
                WHERE
                    NOT EXISTS (
                        SELECT
                            id
                        FROM
                            tmp_renamed_df b
                        WHERE
                            a.id = b.id

                    )
                """).show()

# COMMAND ----------

def convert_to_yes_no(id_col: str) -> str:
    """
    Returns a Yes/No value for given 1/0.
    """
    return F.when(id_col == 1, 'Yes').otherwise(F.when(id_col == 0, 'No').otherwise(None))

# COMMAND ----------

def get_healthcare_result_table(test_name: str) -> DataFrame:
    """
    Generates a test specific result table based off of curated.result_base table.
    """
    df = spark.sql(f"""
    select
       res.result_base_pk
       ,res.raw_table_id
       ,res.healthcare_product_name
       ,ato.id AS ato_id
       ,ato.value AS ato_value
       ,o.id AS o_id
       ,o.description AS o_description
    from
      curated.result_base res
      INNER JOIN transformed.assessment_test_outcome ato ON ato.assessment_test_id = res.assessment_id
      AND ato.healthcare_product_name = res.healthcare_product_name
      INNER JOIN transformed.outcome o ON ato.outcome_id = o.Id
      AND o.healthcare_product_name = res.healthcare_product_name
      WHERE res.test = '{test_name}'
;
  """)
    
    #pivotting on outcome descriptions e.g. Accuracy, Legal Errors, Total Correct, etc.
    grouped_df = df.groupBy(['result_base_pk']).pivot('o_description').agg(F.max('ato_value'))
    
    #joining the grouped_df to original dataframe 
    joined_df = (df.drop('ato_value', 'ato_id', 'o_id', 'o_description').dropDuplicates()                        
            .join(grouped_df, how='inner', on=['result_base_pk']))
    
    #standardizing the column names post pivot 
    for col in joined_df.columns:
        joined_df = joined_df.withColumnRenamed(col, camel_to_snake_case(col))
    
    #converting some 0/1 values to No/Yes as expected with current results: during UAT, stakeholders can be asked if these can redone to boolean
    joined_df = (joined_df
             .withColumn('test_completion', convert_to_yes_no(F.col('test_completion')))
             .withColumn('test_performance', convert_to_yes_no(F.col('test_performance')))
             .withColumn('test_integrity', convert_to_yes_no(F.col('test_integrity')))
                )
    
    return joined_df

# COMMAND ----------

def parallel_run(mapper, items, apply_flat_map=False):
    """
    Invoke the parallel execution of a function
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(mapper, items)
        results = list(results)
        if apply_flat_map:
            results = list(itertools.chain(*results)) # flat map
        return results

# COMMAND ----------

def generate_create_table_script(source_table: str = None, cols_to_rename: dict = {}, add_cols: list = []) -> None:
    """
    Reads a source table as a dataframe and injects the dataframe into target table.
    """
    df = ct_raw_to_transformed_df(source_table, cols_to_rename)
    
    if add_cols:
        for column in add_cols:
            df = df.withColumn(column, F.lit(None))
            

    query_str = ''

    for col_info in df.dtypes:
        query_str += f'{col_info[0]} {col_info[1]},' + '\n'
        
    
    query_str += 'update_dtc timestamp,\n ingestion_dtc timestamp,\n change_status string'
    target_table_name = source_table.split('.')[1]
    full_query = f"""
                CREATE TABLE IF NOT EXISTS transformed.{target_table_name} (\n{query_str})\n
                USING DELTA
                LOCATION "abfss://datalakestore@storage_account_name.dfs.core.windows.net/Transformed/{target_table_name}/"\n
               ;
               """
    
    return full_query.replace('storage_account_name', '{storage_account_name}')

# COMMAND ----------

def rectify_study_name(study_name: str) -> str:
    """
    Update study_name (in CPA study tables) to a format matching sharepoint study listing. 'PeriwinkleCushion' -> 'Periwinkle Cushion' for example.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', study_name) if ' ' not in study_name and '-' not in study_name and '_' not in study_name else study_name

rectify_study_name_udf = udf(rectify_study_name)
