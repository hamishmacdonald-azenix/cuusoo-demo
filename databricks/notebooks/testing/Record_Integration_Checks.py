# Databricks notebook source
# MAGIC %md
# MAGIC This notebook runs a range of integration checks to test that the right records are flowing through correctly to the transformed AND curated layer tables FROM the raw AND transformed layers.

# COMMAND ----------

# DBTITLE 1,Running Spark configuration
# MAGIC %run ../../../notebooks/config/Spark_Config

# COMMAND ----------

# DBTITLE 1,Importing local functions
# MAGIC %run ../../../notebooks/Functions_Collection

# COMMAND ----------

# DBTITLE 1,Testing Transformed Master QS
spark.sql(""" 
WITH study_list AS
(
SELECT
  T.INTERNAL_STUDY_NAME AS INTERNALSTDYNM
  ,T.PROTOCOL_NUMBER AS PROTOCOLNUM
  ,T.IS_GENERAL_RESEARCH_ACCESS_ALLOWED_FOR_THIS_STUDY_DATA AS GENERALRESEARCHACCESS  
  ,T.IS_THIS_STUDY_CURRENTLY_ACTIVE AS ACTIVESTUDY
FROM
  raw.clinical_trials_study_list T
  INNER JOIN 
  (
    SELECT
      MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
    FROM
      raw.clinical_trials_study_list
  ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
), 
study_mapping AS
(
SELECT
  SOURCE_NAME,
  STANDARDISED_NAME
FROM
  raw.clinical_trials_main_study_mapping T
  INNER JOIN (
    SELECT
      MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
    FROM
      raw.clinical_trials_main_study_mapping
  ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
),
latest_sas_files AS
(
SELECT
  COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) AS STDYNM,
  MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
FROM
  raw.clinical_ink_sas_files S
  LEFT OUTER JOIN study_mapping SM ON COALESCE(S.STDYNM, S.STUDYNM) = SM.SOURCE_NAME
GROUP BY
  COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM)
)

-- Get the final results
SELECT
  STDYNM
  ,SITENUM
  ,COUNTRY
  ,SCRNUM
  ,VISITNUM
  ,VISITNM
  ,FORMNM
  ,QSLANG
  ,VERSION
  ,QSDTC
  ,QSTESTCD
  ,QSTEST
  ,QSORRES
  ,QSND
  ,QSREASND
  ,QSRATER
  ,RAW_TABLE_ID
  ,CK
  ,QS_PK
  ,GENERALRESEARCHACCESS
  ,ACTIVESTUDY
  ,INTERNALSTDYNM
FROM
  (
  SELECT
    LSF.STDYNM
    ,S.SITENUM
    ,S.COUNTRY
    ,S.SCRNUM
    ,S.VISITNUM
    ,S.VISITNM
    ,S.FORMNM
    ,CASE 
          WHEN S.QSLANG = '' 
          THEN NULL 
          ELSE S.QSLANG 
      END AS QSLANG
    ,S.VERSION
    ,COALESCE(to_timestamp(S.QSDTC), to_timestamp(S.QSDTC, 'dd-MMM-yyyy'), to_timestamp(S.QSDTC, 'm/dd/yyyy')) AS QSDTC
    ,S.QSTESTCD
    ,S.QSTEST
    ,CASE
        WHEN S.QSORRES = ''
        THEN NULL
        ELSE S.QSORRES
    END AS QSORRES
    ,CASE 
          WHEN S.QSND = '' 
          THEN NULL 
          ELSE S.QSND 
      END AS QSND
    ,CASE 
          WHEN S.QSREASND = '' 
          THEN NULL 
          ELSE S.QSREASND 
      END AS QSREASND
    ,CASE 
         WHEN S.QSRATER = '' 
         THEN NULL 
         ELSE S.QSRATER 
     END AS QSRATER
    ,S.RAW_PK AS RAW_TABLE_ID
    ,CONCAT(COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM), S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) AS CK
    ,UUID() AS QS_PK
    ,ROW_NUMBER() OVER(PARTITION BY CONCAT(COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM), S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) ORDER BY (CASE WHEN S.QSORRES = '' THEN NULL ELSE S.QSORRES END) DESC) AS ROW_NUMBER
    ,SL.GENERALRESEARCHACCESS
    ,SL.ACTIVESTUDY
    ,SL.INTERNALSTDYNM
  FROM
    raw.clinical_ink_sas_files S
    LEFT OUTER JOIN study_mapping SM ON COALESCE(S.STDYNM, S.STUDYNM) = SM.SOURCE_NAME
    INNER JOIN latest_sas_files LSF ON COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) = LSF.STDYNM
      AND LSF.RAW_FILELOADDATE = S.RAW_FILELOADDATE
    LEFT OUTER JOIN study_list SL ON COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) = SL.PROTOCOLNUM
  WHERE
    COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) IS NOT NULL
  ) S
WHERE
  ROW_NUMBER = 1
  AND CONCAT(S.STDYNM, S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) IS NOT NULL
""").createOrReplaceTempView("qs_view")

def test_transformed_main_qs():
    print ('testing transformed.main_qs record counts...')
    assert spark.sql("select count(*) FROM transformed.main_qs").collect()[0][0] == spark.sql("select count(*) FROM qs_view").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed Master LR10
spark.sql(""" 
WITH study_list AS
(
SELECT
  T.INTERNAL_STUDY_NAME AS INTERNALSTDYNM
  ,T.PROTOCOL_NUMBER AS PROTOCOLNUM
  ,T.IS_GENERAL_RESEARCH_ACCESS_ALLOWED_FOR_THIS_STUDY_DATA AS GENERALRESEARCHACCESS  
  ,T.IS_THIS_STUDY_CURRENTLY_ACTIVE AS ACTIVESTUDY
FROM
  raw.clinical_trials_study_list T
  INNER JOIN 
  (
    SELECT
      MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
    FROM
      raw.clinical_trials_study_list
  ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
), 
study_mapping AS
(
SELECT
  SOURCE_NAME,
  STANDARDISED_NAME
FROM
  raw.clinical_trials_main_study_mapping T
  INNER JOIN (
    SELECT
      MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
    FROM
      raw.clinical_trials_main_study_mapping
  ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
),
latest_excel_files AS
(
SELECT
  COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) AS PROTOCOL_NUMBER
  ,MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
FROM
  raw.clinical_ink_excel_reports S
  LEFT OUTER JOIN study_mapping SM ON S.PROTOCOL_NUMBER = SM.SOURCE_NAME
GROUP BY
  COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER)
)

-- Get the final results
SELECT
  CASE
     WHEN S.VISIT_FORM_ID IS NULL
     THEN MD5(CONCAT(S.PROTOCOL_NUMBER, S.SITE_NUMBER, S.SCREENING_NUMBER, S.VISIT_NAME, S.FORM_NAME, ROW_NUMBER() OVER(PARTITION BY S.PROTOCOL_NUMBER, S.SITE_NUMBER, S.SCREENING_NUMBER, S.VISIT_NAME, S.FORM_NAME ORDER BY FIRST_COMPLETED_EDITED_DATE)))
     ELSE S.VISIT_FORM_ID
   END AS VISIT_FORM_ID
FROM
  raw.clinical_ink_excel_reports S
  LEFT OUTER JOIN study_mapping SM ON S.PROTOCOL_NUMBER = SM.SOURCE_NAME
  INNER JOIN latest_excel_files LEF ON COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) = LEF.PROTOCOL_NUMBER
    AND LEF.RAW_FILELOADDATE = S.RAW_FILELOADDATE
  LEFT OUTER JOIN study_list SL ON COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) = SL.PROTOCOLNUM
WHERE
  COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) IS NOT NULL
""").createOrReplaceTempView("lr10_view")

def test_transformed_main_lr10():
    print ('testing transformed.main_lr10 record counts...')
    assert spark.sql("select count(*) FROM transformed.main_lr10").collect()[0][0] == spark.sql("select count(*) FROM lr10_view").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Studies
def test_curated_main_studies():
    print ('testing curated.main_studies record counts...')
    assert spark.sql("select count(*) FROM curated.main_studies").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_study_list where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_study_list)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Study Sites
def test_curated_main_study_sites():
    print ('testing curated.main_study_sites record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_sites").collect()[0][0] == spark.sql("select count(distinct stdynm, sitenum) FROM transformed.main_qs").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Study Subjects
def test_curated_main_study_subjects():
    print ('testing curated.main_study_subjects record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_subjects").collect()[0][0] == spark.sql("select count(distinct stdynm, sitenum, scrnum) FROM transformed.main_qs").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Study Visits
def test_curated_main_study_visits():
    print ('testing curated.main_study_visits record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_visits").collect()[0][0] == spark.sql("select count(distinct stdynm, sitenum, scrnum, visitnm) FROM transformed.main_qs").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Raters
def test_curated_main_raters():
    print ('testing curated.main_raters record counts...')
    assert spark.sql("select count(*) FROM curated.main_raters").collect()[0][0] == spark.sql("select count(distinct rater_email_address) from transformed.main_lr10 where rater_email_address <> 'nan' and rater_email_address IS NOT NULL").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Scaleforms
def test_curated_main_scaleforms():
    print ('testing curated.main_scaleforms record counts...')
    assert spark.sql("select count(*) FROM curated.main_scaleforms").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_scale_list where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_scale_list)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Master Items
def test_curated_main_items():
    print ('testing curated.main_items record counts...')
    assert spark.sql("select count(*) FROM curated.main_items").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_items where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_items)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Reference Study Scales
def test_curated_reference_study_scales():
    print ('testing curated.reference_study_scales record counts...')
    assert spark.sql("select count(*) FROM curated.reference_study_scales").collect()[0][0] == spark.sql("select count(distinct internal_study_name, scale) FROM curated.result_scale_base").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Reference Visit Labels
def test_curated_reference_visit_labels():
    print ('testing curated.reference_visit_labels record counts...')
    assert spark.sql("select count(*) FROM curated.reference_visit_labels").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_visit_labels where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_visit_labels)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Reference Unusual Score Thresholds
def test_curated_reference_unusual_score_thresholds():
    print ('testing curated.reference_unusual_score_thresholds record counts...')
    assert spark.sql("select count(*) FROM curated.reference_unusual_score_thresholds").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_unusual_score_thresholds where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_unusual_score_thresholds)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result Base
def test_curated_result_scale_base():
    print ('testing curated.result_scale_base record counts...')
    assert spark.sql("select count(*) FROM curated.result_scale_base").collect()[0][0] == spark.sql("select count(distinct(M.stdynm,M.sitenum,M.scrnum,M.visitnm,M.formnm)) FROM transformed.main_qs M WHERE M.formnm like '%ADAS%' or M.formnm like'%ADCS%' or M.formnm like '%CDR%' or M.formnm like'%MMSE%' or M.formnm like'%WAIS%' or M.formnm like'%Mini-Mental%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result ADAS-Cog
def test_curated_result_adas_cog():
    print ('testing curated.result_adas_cog record counts...')
    assert spark.sql("select count(*) FROM curated.result_adas_cog").collect()[0][0] == spark.sql("select count(distinct stdynm,sitenum,scrnum,visitnm,formnm) FROM transformed.main_qs where formnm like '%ADAS%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result ADCS-ADL
def test_curated_result_adcs_adl():
    print ('testing curated.result_adcs_adl record counts...')
    assert spark.sql("select count(*) FROM curated.result_adcs_adl").collect()[0][0] == spark.sql("select count(distinct stdynm,sitenum,scrnum,visitnm,formnm) FROM transformed.main_qs where formnm like '%ADL%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result CDR
def test_curated_result_cdr():
    print ('testing curated.result_cdr record counts...')
    assert spark.sql("select count(*) FROM curated.result_cdr").collect()[0][0] == spark.sql("select count(distinct stdynm,sitenum,scrnum,visitnm,formnm) FROM transformed.main_qs where formnm like '%CDR%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result MMSE
def test_curated_result_mmse():
    print ('testing curated.result_mmse record counts...')
    assert spark.sql("select count(*) FROM curated.result_mmse").collect()[0][0] == spark.sql("select count(distinct stdynm,sitenum,scrnum,visitnm,formnm) FROM transformed.main_qs where formnm like '%MMSE%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result WAIS-IV DSC
def test_curated_result_wais_iv_dsc():
    print ('testing curated.result_wais_iv_dsc record counts...')
    assert spark.sql("select count(*) FROM curated.result_wais_iv_dsc").collect()[0][0] == spark.sql("select count(distinct stdynm,sitenum,scrnum,visitnm,formnm) FROM transformed.main_qs where formnm like '%WAIS%'").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Main Leads Study
def test_curated_main_study_leads():
    print ('testing curated.main_study_leads record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_leads").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_lead_study_assignment").collect()[0][0]
    

# COMMAND ----------

# DBTITLE 1,Testing Curated Main Leads
def test_curated_main_leads():
    print ('testing curated.main_leads record counts...')
    assert spark.sql("select count(*) FROM curated.main_leads").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_lead").collect()[0][0]
    

# COMMAND ----------

# DBTITLE 1,Testing Curated Main Raters Studies
def test_curated_main_study_raters():
    print ('testing curated.main_study_raters record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_raters").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_rater").collect()[0][0]
    

# COMMAND ----------

# DBTITLE 1,Testing Curated Main Study SRFS
def test_curated_main_study_srfs():
    print ('testing curated.main_study_srfs record counts...')
    assert spark.sql("select count(*) FROM curated.main_study_srfs").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_scale_review_form").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result SRF Science Changes 
def test_curated_result_srf_science_changes():
    print ('testing curated.result_srf_science_changes record counts...')
    assert spark.sql("select count(*) FROM curated.result_srf_science_changes").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_history_annotation").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result SRF Items
def test_curated_result_srf_items():
    print ('testing curated.result_srf_items record counts...')
    assert spark.sql("select count(*) FROM curated.result_srf_items").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_review_item_response").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result SRF 
def test_curated_result_srf():
    print ('testing curated.result_srf record counts...')
    assert spark.sql("select count(*) FROM curated.result_srf").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_scale_review_form_review").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Result SRF Score Changes 
def test_curated_result_srf_score_changes():
    print ('testing curated.result_srf_score_changes record counts...')
    assert spark.sql("select count(*) FROM curated.result_srf_score_changes").collect()[0][0] == spark.sql("select count(distinct id) FROM transformed.carp_score_change_query").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Curated Reference Scale Multiplicand 
def test_curated_reference_scale_multiplicand():
    print ('testing curated.reference_scale_multiplicand record counts...')
    assert spark.sql("select count(*) FROM curated.reference_scale_multiplicand").collect()[0][0] == spark.sql("select count(*) FROM raw.clinical_trials_scale_multiplicand where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_scale_multiplicand)").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP History Annotation 
def test_transformed_carp_history_annotation():
    print ('testing transformed.carp_history_annotation record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_history_annotation").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_historyannotation").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Lead
def test_transformed_carp_lead():
    print ('testing transformed.carp_lead record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_lead").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_lead").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Lead Study Assignment
def test_transformed_carp_lead_study_assignment():
    print ('testing transformed.carp_lead_study_assignment record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_lead_study_assignment").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_leadstudyassignment").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Question
def test_transformed_carp_question():
    print ('testing transformed.carp_question record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_question").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_question").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Rater
def test_transformed_carp_rater():
    print ('testing transformed.carp_rater record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_rater").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_rater").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Remediation
def test_transformed_carp_remediation():
    print ('testing transformed.carp_remediation record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_remediation").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_remediation").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Review Item Response
def test_transformed_carp_review_item_response():
    print ('testing transformed.carp_review_item_response record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_review_item_response").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_reviewitemresponse").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Scale Review Form
def test_transformed_carp_scale_review_form():
    print ('testing transformed.carp_scale_review_form record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_scale_review_form").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_scalereviewform").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Scale Review Form Review
def test_transformed_carp_scale_review_form_review():
    print ('testing transformed.carp_scale_review_form_review record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_scale_review_form_review").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_scalereviewformreview").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Score Change Query
def test_transformed_carp_score_change_query():
    print ('testing transformed.carp_score_change_query record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_score_change_query").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_scorechangequery").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Score Change Request
def test_transformed_carp_score_change_request():
    print ('testing transformed.carp_score_change_request record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_score_change_request").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_scorechangerequest").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Study
def test_transformed_carp_study():
    print ('testing transformed.carp_study record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_study").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_study").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Testing Transformed CARP Review
def test_transformed_carp_review():
    print ('testing transformed.carp_review record counts...')
    assert spark.sql("select count(*) FROM transformed.carp_review").collect()[0][0] == spark.sql("select count(distinct id) FROM raw.carp_dbo_review").collect()[0][0]

# COMMAND ----------

# DBTITLE 1,Executing tests
test_transformed_main_qs()
test_transformed_main_lr10()
test_curated_main_studies()
test_curated_main_study_sites()
test_curated_main_study_subjects()
test_curated_main_study_visits()
test_curated_main_raters()
test_curated_main_scaleforms()
test_curated_main_items()
test_curated_reference_study_scales()
test_curated_reference_visit_labels()
test_curated_reference_unusual_score_thresholds()
test_curated_result_scale_base()
test_curated_result_adas_cog()
test_curated_result_adcs_adl()
test_curated_result_cdr()
test_curated_result_mmse()
test_curated_result_wais_iv_dsc()
test_curated_main_study_leads()
test_curated_main_leads()
test_curated_main_study_raters()
test_curated_main_study_srfs()
test_curated_result_srf_science_changes()
test_curated_result_srf_items()
test_curated_result_srf()
test_curated_result_srf_score_changes()
test_curated_reference_scale_multiplicand()
test_transformed_carp_history_annotation()
test_transformed_carp_lead()
test_transformed_carp_lead_study_assignment()
test_transformed_carp_question()
test_transformed_carp_rater()
test_transformed_carp_remediation()
test_transformed_carp_review_item_response()
test_transformed_carp_scale_review_form()
test_transformed_carp_scale_review_form_review()
test_transformed_carp_score_change_query()
test_transformed_carp_score_change_request()
test_transformed_carp_study()
test_transformed_carp_review()

# COMMAND ----------

# DBTITLE 1,Uncomment and run this for an overview of actual versus expected counts for all tables (as of 24/05/2022)
# %sql

# SELECT *, CASE WHEN actual_count = expected_count THEN 'Pass' ELSE 'Fail' END AS result FROM(

# --curated.main_qs
# select 
#   'transformed' as layer
#   ,'main_qs' as table_name
#   ,(select count(*) FROM transformed.main_qs) as actual_count
#   ,count(*) as expected_count
# From(WITH study_list AS
# (
# SELECT
#   T.INTERNAL_STUDY_NAME AS INTERNALSTDYNM
#   ,T.PROTOCOL_NUMBER AS PROTOCOLNUM
#   ,T.IS_GENERAL_RESEARCH_ACCESS_ALLOWED_FOR_THIS_STUDY_DATA AS GENERALRESEARCHACCESS  
#   ,T.IS_THIS_STUDY_CURRENTLY_ACTIVE AS ACTIVESTUDY
# FROM
#   raw.clinical_trials_study_list T
#   INNER JOIN 
#   (
#     SELECT
#       MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
#     FROM
#       raw.clinical_trials_study_list
#   ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
# ), 
# study_mapping AS
# (
# SELECT
#   SOURCE_NAME,
#   STANDARDISED_NAME
# FROM
#   raw.clinical_trials_main_study_mapping T
#   INNER JOIN (
#     SELECT
#       MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
#     FROM
#       raw.clinical_trials_main_study_mapping
#   ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
# ),
# latest_sas_files AS
# (
# SELECT
#   COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) AS STDYNM,
#   MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
# FROM
#   raw.clinical_ink_sas_files S
#   LEFT OUTER JOIN study_mapping SM ON COALESCE(S.STDYNM, S.STUDYNM) = SM.SOURCE_NAME
# GROUP BY
#   COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM)
# )

# -- Get the final results
# SELECT
#   STDYNM
#   ,SITENUM
#   ,COUNTRY
#   ,SCRNUM
#   ,VISITNUM
#   ,VISITNM
#   ,FORMNM
#   ,QSLANG
#   ,VERSION
#   ,QSDTC
#   ,QSTESTCD
#   ,QSTEST
#   ,QSORRES
#   ,QSND
#   ,QSREASND
#   ,QSRATER
#   ,RAW_TABLE_ID
#   ,CK
#   ,QS_PK
#   ,GENERALRESEARCHACCESS
#   ,ACTIVESTUDY
#   ,INTERNALSTDYNM
# FROM
#   (
#   SELECT
#     LSF.STDYNM
#     ,S.SITENUM
#     ,S.COUNTRY
#     ,S.SCRNUM
#     ,S.VISITNUM
#     ,S.VISITNM
#     ,S.FORMNM
#     ,CASE 
#           WHEN S.QSLANG = '' 
#           THEN NULL 
#           ELSE S.QSLANG 
#       END AS QSLANG
#     ,S.VERSION
#     ,COALESCE(to_timestamp(S.QSDTC), to_timestamp(S.QSDTC, 'dd-MMM-yyyy'), to_timestamp(S.QSDTC, 'm/dd/yyyy')) AS QSDTC
#     ,S.QSTESTCD
#     ,S.QSTEST
#     ,CASE
#         WHEN S.QSORRES = ''
#         THEN NULL
#         ELSE S.QSORRES
#     END AS QSORRES
#     ,CASE 
#           WHEN S.QSND = '' 
#           THEN NULL 
#           ELSE S.QSND 
#       END AS QSND
#     ,CASE 
#           WHEN S.QSREASND = '' 
#           THEN NULL 
#           ELSE S.QSREASND 
#       END AS QSREASND
#     ,CASE 
#          WHEN S.QSRATER = '' 
#          THEN NULL 
#          ELSE S.QSRATER 
#      END AS QSRATER
#     ,S.RAW_PK AS RAW_TABLE_ID
#     ,CONCAT(COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM), S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) AS CK
#     ,UUID() AS QS_PK
#     ,ROW_NUMBER() OVER(PARTITION BY CONCAT(COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM), S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) ORDER BY (CASE WHEN S.QSORRES = '' THEN NULL ELSE S.QSORRES END) DESC) AS ROW_NUMBER
#     ,SL.GENERALRESEARCHACCESS
#     ,SL.ACTIVESTUDY
#     ,SL.INTERNALSTDYNM
#   FROM
#     raw.clinical_ink_sas_files S
#     LEFT OUTER JOIN study_mapping SM ON COALESCE(S.STDYNM, S.STUDYNM) = SM.SOURCE_NAME
#     INNER JOIN latest_sas_files LSF ON COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) = LSF.STDYNM
#       AND LSF.RAW_FILELOADDATE = S.RAW_FILELOADDATE
#     LEFT OUTER JOIN study_list SL ON COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) = SL.PROTOCOLNUM
#   WHERE
#     COALESCE(SM.STANDARDISED_NAME, S.STDYNM, S.STUDYNM) IS NOT NULL
#   ) S
# WHERE
#   ROW_NUMBER = 1
#   AND CONCAT(S.STDYNM, S.SITENUM, S.SCRNUM, S.VISITNM, S.FORMNM, S.QSTESTCD) IS NOT NULL)

# UNION
# --curated.main_lr10
# select 
#   'transformed' as layer
#   ,'main_lr10' as table_name
#   ,(select count(*) FROM transformed.main_lr10) as actual_count
#   ,count(*) as expected_count
# From(WITH study_list AS
# (
# SELECT
#   T.INTERNAL_STUDY_NAME AS INTERNALSTDYNM
#   ,T.PROTOCOL_NUMBER AS PROTOCOLNUM
#   ,T.IS_GENERAL_RESEARCH_ACCESS_ALLOWED_FOR_THIS_STUDY_DATA AS GENERALRESEARCHACCESS  
#   ,T.IS_THIS_STUDY_CURRENTLY_ACTIVE AS ACTIVESTUDY
# FROM
#   raw.clinical_trials_study_list T
#   INNER JOIN 
#   (
#     SELECT
#       MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
#     FROM
#       raw.clinical_trials_study_list
#   ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
# ), 
# study_mapping AS
# (
# SELECT
#   SOURCE_NAME,
#   STANDARDISED_NAME
# FROM
#   raw.clinical_trials_main_study_mapping T
#   INNER JOIN (
#     SELECT
#       MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
#     FROM
#       raw.clinical_trials_main_study_mapping
#   ) LatestLoad ON LatestLoad.RAW_FILELOADDATE = T.RAW_FILELOADDATE
# ),
# latest_excel_files AS
# (
# SELECT
#   COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) AS PROTOCOL_NUMBER
#   ,MAX(RAW_FILELOADDATE) AS RAW_FILELOADDATE
# FROM
#   raw.clinical_ink_excel_reports S
#   LEFT OUTER JOIN study_mapping SM ON S.PROTOCOL_NUMBER = SM.SOURCE_NAME
# GROUP BY
#   COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER)
# )

# -- Get the final results
# SELECT
#   CASE
#      WHEN S.VISIT_FORM_ID IS NULL
#      THEN MD5(CONCAT(S.PROTOCOL_NUMBER, S.SITE_NUMBER, S.SCREENING_NUMBER, S.VISIT_NAME, S.FORM_NAME, ROW_NUMBER() OVER(PARTITION BY S.PROTOCOL_NUMBER, S.SITE_NUMBER, S.SCREENING_NUMBER, S.VISIT_NAME, S.FORM_NAME ORDER BY FIRST_COMPLETED_EDITED_DATE)))
#      ELSE S.VISIT_FORM_ID
#    END AS VISIT_FORM_ID
   
# FROM
#   raw.clinical_ink_excel_reports S
#   LEFT OUTER JOIN study_mapping SM ON S.PROTOCOL_NUMBER = SM.SOURCE_NAME
#   INNER JOIN latest_excel_files LEF ON COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) = LEF.PROTOCOL_NUMBER
#     AND LEF.RAW_FILELOADDATE = S.RAW_FILELOADDATE
#   LEFT OUTER JOIN study_list SL ON COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) = SL.PROTOCOLNUM
# WHERE
#   COALESCE(SM.STANDARDISED_NAME, S.PROTOCOL_NUMBER) IS NOT NULL)

# UNION
# --curated.main_studies
# select 
#   'curated' as layer
#   ,'main_studies' as table_name
#   ,(select count(*) FROM curated.main_studies) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_study_list where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_study_list)

# UNION
# --curated.main_study_sites
# select 
#   'curated' as layer
#   ,'main_study_sites' as table_name
#   ,(select count(*) FROM curated.main_study_sites) as actual_count
#   ,count(distinct stdynm, sitenum) as expected_count
# FROM transformed.main_qs

# UNION
# --curated.main_study_subjects
# select 
#   'curated' as layer
#   ,'main_study_subjects' as table_name
#   ,(select count(*) FROM curated.main_study_subjects) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum) as expected_count
# FROM transformed.main_qs

# UNION
# --curated.main_study_visits
# select 
#   'curated' as layer
#   ,'main_study_visits' as table_name
#   ,(select count(*) FROM curated.main_study_visits) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm) as expected_count
# FROM transformed.main_qs

# UNION
# --curated.main_scaleforms
# select 
#   'curated' as layer
#   ,'main_scaleforms' as table_name
#   ,(select count(*) FROM curated.main_scaleforms) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_scale_list where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_scale_list)

# UNION
# --curated.main_items
# select 
#   'curated' as layer
#   ,'main_items' as table_name
#   ,(select count(*) FROM curated.main_items) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_items where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_items)

# UNION
# --curated.main_raters
# select 
#   'curated' as layer
#   ,'main_raters' as table_name
#   ,(select count(*) FROM curated.main_raters) as actual_count
#   ,count(distinct rater_email_address) as expected_count
# FROM transformed.main_lr10 where rater_email_address <> 'nan' and rater_email_address IS NOT NULL

# UNION
# --curated.main_study_raters
# select 
#   'curated' as layer
#   ,'main_study_raters' as table_name
#   ,(select count(*) FROM curated.main_study_raters) as actual_count
#   ,count(*) as expected_count
# FROM transformed.carp_rater

# UNION
# --curated.main_leads
# select 
#   'curated' as layer
#   ,'main_leads' as table_name
#   ,(select count(*) FROM curated.main_leads) as actual_count
#   ,count(*) as expected_count
# FROM transformed.carp_lead

# UNION
# --curated.main_study_leads
# select 
#   'curated' as layer
#   ,'main_study_leads' as table_name
#   ,(select count(*) FROM curated.main_study_leads) as actual_count
#   ,count(*) as expected_count
# FROM transformed.carp_lead_study_assignment

# UNION
# --curated.main_study_srfs
# select 
#   'curated' as layer
#   ,'main_study_srfs' as table_name
#   ,(select count(*) FROM curated.main_study_srfs) as actual_count
#   ,count(*) as expected_count
# FROM transformed.carp_scale_review_form

# UNION
# --curated.reference_unusual_score_thresholds
# select 
#   'curated' as layer
#   ,'reference_unusual_score_thresholds' as table_name
#   ,(select count(*) FROM curated.reference_unusual_score_thresholds) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_unusual_score_thresholds where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_unusual_score_thresholds)

# UNION
# --curated.reference_visit_labels
# select 
#   'curated' as layer
#   ,'reference_visit_labels' as table_name
#   ,(select count(*) FROM curated.reference_visit_labels) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_visit_labels where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_visit_labels)

# UNION
# --curated.reference_scale_multiplicand
# select 
#   'curated' as layer
#   ,'reference_scale_multiplicand' as table_name
#   ,(select count(*) FROM curated.reference_scale_multiplicand) as actual_count
#   ,count(*) as expected_count
# FROM raw.clinical_trials_scale_multiplicand where RAW_FILELOADDATE = (select MAX(RAW_FILELOADDATE) FROM raw.clinical_trials_scale_multiplicand)

# UNION
# --curated.reference_study_scales
# select 
#   'curated' as layer
#   ,'reference_study_scales' as table_name
#   ,(select count(*) FROM curated.reference_study_scales) as actual_count
#   ,count(distinct internal_study_name, scale) as expected_count
# FROM curated.result_scale_base 

# UNION
# --curated.result_scale_base
# select 
#   'curated' as layer
#   ,'result_scale_base' as table_name
#   ,(select count(*) FROM curated.result_scale_base) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs a
# WHERE a.formnm like '%ADAS%' or a.formnm like'%ADCS%' or a.formnm like '%CDR%' or a.formnm like'%MMSE%' or a.formnm like'%WAIS%' or a.formnm like'%Mini-Mental%'

# UNION
# --curated.result_adas_cog
# select 
#   'curated' as layer
#   ,'result_adas_cog' as table_name
#   ,(select count(*) FROM curated.result_adas_cog) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs 
# where formnm like '%ADAS%'

# UNION
# --curated.result_adcs_adl
# select 
#   'curated' as layer
#   ,'result_adcs_adl' as table_name
#   ,(select count(*) FROM curated.result_adcs_adl) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs 
# where formnm like '%ADL%'

# UNION
# --curated.result_cdr
# select 
#   'curated' as layer
#   ,'result_cdr' as table_name
#   ,(select count(*) FROM curated.result_cdr) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs 
# where formnm like '%CDR%'

# UNION
# --curated.result_mmse
# select 
#   'curated' as layer
#   ,'result_mmse' as table_name
#   ,(select count(*) FROM curated.result_mmse) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs 
# where formnm like '%MMSE%'

# UNION
# --curated.result_wais_iv_dsc
# select 
#   'curated' as layer
#   ,'result_wais_iv_dsc' as table_name
#   ,(select count(*) FROM curated.result_wais_iv_dsc) as actual_count
#   ,count(distinct stdynm, sitenum, scrnum, visitnm, formnm) as expected_count
# FROM transformed.main_qs 
# where formnm like '%WAIS%'


# UNION
# --curated.result_srf_science_changes
# select 
#   'curated' as layer
#   ,'result_srf_science_changes' as table_name
#   ,(select count(*) FROM curated.result_srf_science_changes) as actual_count
#   ,count(distinct id) as expected_count
# FROM transformed.carp_history_annotation 

# UNION
# --curated.result_srf_items
# select 
#   'curated' as layer
#   ,'result_srf_items' as table_name
#   ,(select count(*) FROM curated.result_srf_items) as actual_count
#   ,count(distinct id) as expected_count
# FROM transformed.carp_review_item_response 

# UNION
# --curated.result_srf
# select 
#   'curated' as layer
#   ,'result_srf' as table_name
#   ,(select count(*) FROM curated.result_srf) as actual_count
#   ,count(distinct id) as expected_count
# FROM transformed.carp_scale_review_form_review 

# UNION
# --curated.result_srf_score_changes
# select 
#   'curated' as layer
#   ,'result_srf_score_changes' as table_name
#   ,(select count(*) FROM curated.result_srf_score_changes) as actual_count
#   ,count(distinct id) as expected_count
# FROM transformed.carp_score_change_query 

# UNION
# --transformed.carp_history_annotation
# select 
#   'transformed' as layer
#   ,'carp_history_annotation' as table_name
#   ,(select count(*) FROM transformed.carp_history_annotation) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_historyannotation 

# UNION
# --transformed.carp_lead
# select 
#   'transformed' as layer
#   ,'carp_lead' as table_name
#   ,(select count(*) FROM transformed.carp_lead) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_lead 

# UNION
# --transformed.carp_lead_study_assignment
# select 
#   'transformed' as layer
#   ,'carp_lead_study_assignment' as table_name
#   ,(select count(*) FROM transformed.carp_lead_study_assignment) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_leadstudyassignment 

# UNION
# --transformed.carp_question
# select 
#   'transformed' as layer
#   ,'carp_question' as table_name
#   ,(select count(*) FROM transformed.carp_question) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_question 

# UNION
# --transformed.carp_rater
# select 
#   'transformed' as layer
#   ,'carp_rater' as table_name
#   ,(select count(*) FROM transformed.carp_rater) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_rater 

# UNION
# --transformed.carp_remediation
# select 
#   'transformed' as layer
#   ,'carp_remediation' as table_name
#   ,(select count(*) FROM transformed.carp_remediation) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_remediation 

# UNION
# --transformed.carp_review_item_response
# select 
#   'transformed' as layer
#   ,'carp_review_item_response' as table_name
#   ,(select count(*) FROM transformed.carp_review_item_response) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_reviewitemresponse 

# UNION
# --transformed.carp_scale_review_form
# select 
#   'transformed' as layer
#   ,'carp_scale_review_form' as table_name
#   ,(select count(*) FROM transformed.carp_scale_review_form) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_scalereviewform 

# UNION
# --transformed.carp_scale_review_form_review
# select 
#   'transformed' as layer
#   ,'carp_scale_review_form_review' as table_name
#   ,(select count(*) FROM transformed.carp_scale_review_form_review) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_scalereviewformreview 

# UNION
# --transformed.carp_score_change_query
# select 
#   'transformed' as layer
#   ,'carp_score_change_query' as table_name
#   ,(select count(*) FROM transformed.carp_score_change_query) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_scorechangequery


# UNION
# --transformed.carp_score_change_request
# select 
#   'transformed' as layer
#   ,'carp_score_change_request' as table_name
#   ,(select count(*) FROM transformed.carp_score_change_request) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_scorechangerequest 


# UNION
# --transformed.carp_study
# select 
#   'transformed' as layer
#   ,'carp_study' as table_name
#   ,(select count(*) FROM transformed.carp_study) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_study 

# UNION
# --transformed.carp_review
# select 
#   'transformed' as layer
#   ,'carp_review' as table_name
#   ,(select count(*) FROM transformed.carp_review) as actual_count
#   ,count(distinct id) as expected_count
# FROM raw.carp_dbo_review 

# )
