# Databricks notebook source
# DBTITLE 1,Running Spark configuration
# MAGIC %run ../../../notebooks/config/Spark_Config

# COMMAND ----------

# DBTITLE 1,Importing local functions for testing
# MAGIC %run ../../../notebooks/Functions_Collection

# COMMAND ----------

# DBTITLE 1,Importing the required libraries
import time
from pyspark.sql.types import Row

# COMMAND ----------

# DBTITLE 1,Creating sample dataframe to use in the testing
df = spark.createDataFrame([("col1row1", 34, 6), ("col1row2", 22, 1), ("col1row3", None, 12)], ["a", "b", "c"])

# COMMAND ----------

# DBTITLE 1,Testing Replace_Invalid_Chars Function
def test_replace_invalid_chars():
    print ('testing replace_invalid_chars ...')
    assert replace_invalid_chars("abc,;{}()\n\t=]+'().-?10") == 'abc10'
    assert replace_invalid_chars('abc/10') == 'abc_10'
    assert replace_invalid_chars('abc 10') == 'abc_10'
    assert replace_invalid_chars('stdy_pk') == 'stdy_pk'

# COMMAND ----------

# DBTITLE 1,Testing Convert_SAS_To_Dataframe
def test_convert_sas_to_dataframe():
    print ('testing convert_sas_to_dataframe ...')
    dbfs_path = "/new/unittesting/test.sas7bdat"
    new_df = convert_sas_to_dataframe(file_path=f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/Testing/sas_test.sas7bdat", dbfs_path=dbfs_path)
    assert new_df.columns == ['STDYNM', 'SITENUM', 'SCRNUM', 'VISITNUM', 'VISITNM', 'FORMNM', 'QSLANG', 'QSDTC', 'QSTEST', 'QSORRES', 'QSND', 'RATER']
    #sleeping for 5s to allow enough time for the file to be properly deleted
    time.sleep(5)
    assert os.path.exists(f'/dbfs/{dbfs_path}') == False

# COMMAND ----------

# DBTITLE 1,Testing Convert_CSV_To_Dataframe Function
def test_convert_csv_to_dataframe():
    print ('testing convert_csv_to_dataframe ...')
    dbfs_path = "/unittesting/test.csv"
    new_df = convert_csv_to_dataframe(file_path=f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/Testing/table_columns.csv")
    assert new_df.columns ==['CSHCAPI', 'TEMPORAL', 'HEALTHCARE_CLINICIAN', 'ID', '1', 'NULL5', 'NO', 'INT', 'NULL8', 'NULL9', '1010', '1011', '0', 'NULL13', 'NULL14', 'NULL15', 'NULL16', 'NULL17', 'NULL18', 'NULL19', 'NULL20', 'NULL21', 'NULL22']


# COMMAND ----------

# DBTITLE 1,Testing Convert_XLSX_To_Dataframe Function
def test_convert_xlsx_to_dataframe():
    print ('testing convert_xlsx_to_dataframe ....')
    dbfs_path = "/unittesting/test.xlsx"
    new_df = convert_xlsx_to_dataframe(file_path=f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/Testing/lr10_i5_test.xlsx", dbfs_path=dbfs_path)
    assert new_df.columns == ['SPONSOR', 'PROTOCOL_NUMBER', 'SITE_NUMBER', 'SITE_NAME', 'SCREENING_NUMBER', 'SUBJECT_STATUS', 'VISIT_NAME', 'FORM_NAME', 'VISIT_FORM_ID', 'DERIVED_SCALE_NAME', 'LANGUAGE_THAT_RATER_CHOSE_FROM_A_DROPDOWN_MENU', 'RATER_NAME', 'RATER_USER_NAME', 'METHOD_OF_ADMINISTRATION', 'FORM_STATUS', 'CHECK_IN_STATUS', 'INTENTIONALLY_LEFT_BLANK', 'TEST_ADMINISTRATION_DATE_ON_THE_FORM', 'FIRST_COMPLETED_EDITED_DATE', 'FIRST_COMPLETED_EDITED_TIME', 'FIRST_COMPLETED_EDITED_NAME', 'FIRST_COMPLETEDTEST_ADMINISTERS_INITIAL_ON_THE_FORM', 'LAST_COMPLETED_EDITED_DATE', 'LAST_COMPLETED_EDITED_TIME', 'LAST_COMPLETED_EDITED_NAME', 'LAST_COMPLETEDTEST_ADMINISTERS_INITIAL_ON_THE_FORM', 'AUDIO_FILE_CREATED_BY', 'REVIEW_STATUS_MONITOR', 'REVIEW_DATE_MONITOR', 'REVIEW_NAME_MONITOR', 'REVIEW_STATUS_LEAD', 'REASON_FOR_REVIEW', 'REVIEW_DATE_LEAD', 'REVIEW_NAME_LEAD', 'VALIDATION_OPEN', 'URL']
    #sleeping for 5s to allow enough time for the file to be properly deleted
    time.sleep(5)
    assert os.path.exists(f'/dbfs/{dbfs_path}') == False

# COMMAND ----------

# DBTITLE 1,Testing Read_YML_Config Function
def test_read_yml_config():
    print ('testing read_yml_config ...')
    dbfs_path = "/unittesting/test.yml"
    yml_read = read_yml_config(f"abfss://datalakestore@{storage_account_name}.dfs.core.windows.net/Testing/yaml_test.yml", dbfs_path=dbfs_path)
      
    assert yml_read['systems'][0]['config_path'] == 'Ingestion/SharePoint/File Imports'
    #sleeping for 5s to allow enough time for the file to be properly deleted
    time.sleep(5)
    assert os.path.exists(f'/dbfs/{dbfs_path}') == False


# COMMAND ----------

# DBTITLE 1,Testing Dataframe_Table_Column_Sync Function
def test_dataframe_table_column_sync():
    print ('testing dataframe_table_column_sync ...')
    table_name = 'curated.main_studies'
    new_df = dataframe_table_column_sync(df, table_name)
    #check if column 'a' is dropped in the new_df
    assert 'a' not in new_df.columns
    #check if column 'STDY_PK' is added in the new_df
    assert 'study_pk' in new_df.columns
    #check if column 'STDY_PK' is null (new columns are all added with null values.)
    assert new_df.select('study_pk').distinct().collect()[0][0] == None

# COMMAND ----------

# DBTITLE 1,Testing With_Summed_Rows_Ignoring_Nulls Function
def test_with_summed_rows_ignoring_nulls():
    print ('testing with_summed_rows_ignoring_nulls ...')
    new_df = with_summed_rows_ignoring_nulls(df, 'd', ['b', 'c'])
    assert new_df.select('d').where(F.col('a') == 'col1row3').collect()[0][0] == 12
    assert new_df.select('d').where(F.col('a') == 'col1row1').collect()[0][0] == 40

# COMMAND ----------

# DBTITLE 1,Testing With_Summed_Rows Function
def test_with_summed_rows():
    print ('testing with_summed_rows ...')
    new_df = with_summed_rows(df, 'd', ['b', 'c'])
    assert new_df.select('d').where(F.col('a') == 'col1row3').collect()[0][0] == None
    assert new_df.select('d').where(F.col('a') == 'col1row1').collect()[0][0] == 40

# COMMAND ----------

# DBTITLE 1,Testing Get_Transposed_QS_For_ADAS Function
def test_get_transposed_qs_for_adas():
    print ('testing get_transposed_qs for adas keyword...')
    new_df = get_transposed_qs('ADAS')
    cols_expected = ['adas_cpraxis_circle', 'adas_cpraxis_cube', 'adas_commands_1_fist', 'adas_comprehension', 'adas_drecall_w2']
    for col in cols_expected:
        assert col in new_df.columns

# COMMAND ----------

# DBTITLE 1,Testing Get_Transposed_QS_For_ADCS Function
def test_get_transposed_qs_for_adcs():
    print ('testing get_transposed_qs for adcs keyword...')
    new_df = get_transposed_qs('ADCS')
    cols_expected = ['adlquestion1','adlquestion10','adlquestion11','cdrhobbiesrating','cdricommunityaffairsq1','cdricommunityaffairsq10','cdricommunityaffairsq2','cdricommunityaffairsq3','cdricommunityaffairsq4','cdricommunityaffairsq4a','cdricommunityaffairsq4b','cdricommunityaffairsq5','cdricommunityaffairsq6','cdricommunityaffairsq7','cdricommunityaffairsq8','cdricommunityaffairsq9','cdrijudgmentq1','cdrsorientationratingq2']
    for col in cols_expected:
        assert col in new_df.columns

# COMMAND ----------

# DBTITLE 1,Testing Generic_Table_Merge Function
def test_generic_table_merge():
    spark.sql("""
        CREATE TABLE IF NOT EXISTS data_quality.unit_testing
        (a STRING,
        b INT,
        c INT,
        new TIMESTAMP);
            """)
    
    additional_cols_to_insert = [("new", "current_timestamp()")]

    generic_table_merge(source_data_frame=df, target_table='data_quality.unit_testing' , join_column_list=['a'], update_add_columns=[], insert_add_columns=additional_cols_to_insert, add_missing_columns=True, ignore_for_match_columns=[])
    
    # assert that the values for column a has been correctly inserted into the table
    assert sorted(spark.sql("SELECT DISTINCT(a) FROM data_quality.unit_testing;").collect()) == [Row(a='col1row1'), Row(a='col1row2'), Row(a='col1row3')]
    
    #assert that the table gets a 'new' column name along with the existing columns
    assert spark.table('data_quality.unit_testing').columns == ['a', 'b', 'c', 'new']
    
    spark.sql("""DROP TABLE data_quality.unit_testing""")


# COMMAND ----------

# DBTITLE 1,Testing Get_Filename_Load_Date Function
def test_get_filename_load_date():
    print ('testing get_filename_load_date...')
    assert get_filename_load_date("ADAL _20-20190901") == "20190901"
    assert get_filename_load_date("ADAL-20-2020_ 20190901_qs.sas7bdat") == "20190901"
    assert get_filename_load_date("ADAL-20-2020_ 20190901_qs_2020-ADAL-20200120.sas7bdat") == "20190901"

# COMMAND ----------

# DBTITLE 1,Testing Get_Valid_Study Function
def test_get_valid_study():
    rows = [Row(SOURCE_NAME='NovoNordisk NN7999-3895 P6 Non English Sites', STANDARDISED_NAME='NN7999-3895')]
    standard_studies = [data[1] for data in rows]
    studies_map = {data[0]:data[1] for data in rows}
    assert get_valid_study('NovoNordisk NN7999-3895 P6 Non English Sites', standard_studies, studies_map) == 'NN7999-3895'
    # if a value with no corresponding standard name is provided, same name should be returned
    assert get_valid_study('value not present', standard_studies, studies_map) == 'value not present'

# COMMAND ----------

# DBTITLE 1, Testing Impose_Table_Schema_Dataframe Function
def test_impose_table_schema_dataframe():
    spark.sql('CREATE TABLE IF NOT EXISTS check_schema (a STRING, b STRING, c STRING)')
    existing_df = spark.table('check_schema')
    schema_updated_df = impose_table_schema_dataframe('check_schema', df)
    # the outputted dataframe should be: string, string, string 
    # instead of original schema: string, bigint, bigint
    assert schema_updated_df.dtypes == [('a', 'string'), ('b', 'string'), ('c', 'string')]
    assert df.dtypes == [('a', 'string'), ('b', 'bigint'), ('c', 'bigint')]
    spark.sql('DROP TABLE check_schema')

# COMMAND ----------

# DBTITLE 1, Testing Camel_To_Snake_Case Function
def test_camel_to_snake_case():
    print ('testing camel_to_snake_case ...')
    assert camel_to_snake_case('StdyPk') == 'stdy_pk'
    assert camel_to_snake_case('STDY_PK') == 'stdy_pk'

# COMMAND ----------

# DBTITLE 1,Testing Add_Table_Column Function 
def test_add_table_column():
    print ('testing add_table_column function ...')
    spark.sql("""
    CREATE TABLE IF NOT EXISTS data_quality.add_table_column_test
    (
        id int,
        test string
   );
        """)
    
    old_table_columns = spark.table('data_quality.add_table_column_test').columns
    additional_column = 'testing'
    add_table_column('data_quality.add_table_column_test',additional_column)
    
    assert list(set(spark.table('data_quality.add_table_column_test').columns) - set(old_table_columns))[0] == additional_column
    
    spark.sql(f"DROP TABLE data_quality.add_table_column_test")

# COMMAND ----------

# DBTITLE 1,Testing Drop_Database_Tables Function 
def test_drop_database_tables():
    print ('testing drop_database_tables function ...')
    
    spark.sql("""
        CREATE DATABASE IF NOT EXISTS dbtesting 
    
        """)
    
    spark.sql("""
        CREATE TABLE IF NOT EXISTS dbtesting.test_table1
        (
        id int,
        test string
       );
        """)
    
    drop_database_tables('dbtesting')
    assert len(spark.catalog.listTables('dbtesting')) == 0
    
    spark.sql("""
        DROP DATABASE IF EXISTS dbtesting 
        """)

# COMMAND ----------

# DBTITLE 1,Testing carp_Raw_To_Transfromed_DF Function
def test_carp_raw_to_transformed_df():
    print ('testing carp_raw_to_transformed_df function ...')
    
    spark.sql("""
    CREATE TABLE IF NOT EXISTS data_quality.rater_carp_raw_test
    (
        ID int,
        TEST string,
        RAW_PK string,
        RAW_CHANGESTATUS string, 
        RAW_INGESTIONDTC timestamp, 
        RAW_FILELOADDATE timestamp, 
        RAW_FILENAME string
   );
        """)

    spark.sql("""
    CREATE TABLE IF NOT EXISTS data_quality.carp_raw_to_transformed_df_test
    (id int,
     test string,
     raw_table_id string

   );
        """)
    
    transformed_df = carp_raw_to_transformed_df(source_table = 'data_quality.rater_carp_raw_test')
    
    #assert that the source table columns match the transfromed table columns
    assert transformed_df.columns == spark.table('data_quality.carp_raw_to_transformed_df_test').columns
    
    for table in ['data_quality.rater_carp_raw_test', 'data_quality.carp_raw_to_transformed_df_test']:
        spark.sql(f"DROP TABLE {table}")

# COMMAND ----------

# DBTITLE 1,Testing Rater_Tranformed_Table_Load Function
def test_ct_transformed_table_load():
    print ('testing ct_transformed_table_load function ...')
    spark.sql("""
    CREATE TABLE IF NOT EXISTS data_quality.rater_transformed_table_test
    (
        ID int,
        TEST string,
        RAW_PK string,
        RAW_FILENAME string
   );
        """)

    spark.sql("""
    CREATE TABLE IF NOT EXISTS data_quality.ct_transformed_table_load_test
    (id int,
     test string,
     raw_table_id string,
     change_status string,
     ingestion_dtc timestamp,
     update_dtc timestamp
   );
        """)
            
    spark.sql("""
    INSERT INTO data_quality.rater_transformed_table_test
    VALUES (1, '1x', '1xx', 'Filename1.txt'), (2, '2x', '2xx', 'Filename2.txt');
    """)
    
    ct_transformed_table_load(source_table = 'data_quality.rater_transformed_table_test', target_table = 'data_quality.ct_transformed_table_load_test')
    
    #assert that the value from TEST column in source table is rightly inserted into test column in target table
    assert spark.table('data_quality.ct_transformed_table_load_test').select('test').collect()[1][0] == '2x'
    
    for table in ['data_quality.rater_transformed_table_test', 'data_quality.ct_transformed_table_load_test']:
        spark.sql(f"DROP TABLE {table}")

# COMMAND ----------

if __name__ == "__main__":
    test_replace_invalid_chars()
    test_convert_sas_to_dataframe()
    test_convert_xlsx_to_dataframe()
    test_convert_csv_to_dataframe()
    test_read_yml_config()
    test_dataframe_table_column_sync()
    test_with_summed_rows_ignoring_nulls()
    test_with_summed_rows()
    test_get_transposed_qs_for_adas()
    test_get_transposed_qs_for_adcs()
    test_generic_table_merge()
    test_get_filename_load_date()
    test_get_valid_study()
    test_impose_table_schema_dataframe()
    test_camel_to_snake_case()
    test_add_table_column()
    test_drop_database_tables()
    test_carp_raw_to_transformed_df()
    test_ct_transformed_table_load()
