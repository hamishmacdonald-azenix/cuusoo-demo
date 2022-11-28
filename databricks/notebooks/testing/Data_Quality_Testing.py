# Databricks notebook source
# MAGIC %md
# MAGIC This notebook runs a range of data quality checks to test that the right records are flowing through to the transformed and curated layer tables from the raw and transformed layer.

# COMMAND ----------

# MAGIC %run ../../../notebooks/config/Spark_Config

# COMMAND ----------

# MAGIC %run ../../../notebooks/Functions_Collection

# COMMAND ----------

databases_to_check = ['raw','transformed', 'curated' ]

# COMMAND ----------

for database in databases_to_check:
    for table in spark.catalog.listTables(database):
        print (f'\nshowing records for {database}.{table.name}\n\n')
        spark.table(f'{database}.{table.name}').display()

# COMMAND ----------

# MAGIC %sql
# MAGIC select distinct VISIT_FORM_ID from raw.clinical_ink_excel_reports;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from raw.clinical_trials_study_list

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from raw.clinical_trials_scale_list

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from raw.clinical_trials_items

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from raw.clinical_trials_visit_labels

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from raw.clinical_trials_unusual_score_thresholds

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_visits

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_subjects

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_sites

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_studies

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_raters

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_raters

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_scaleforms

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_items

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_leads

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_leads

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.main_study_srfs

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_adas_cog

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_adcs_adl

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_cdr

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_mmse

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_wais_iv_dsc

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_srf_science_changes

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_srf_items

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_srf

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.result_srf_score_changes

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.reference_visit_labels

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.reference_unusual_score_thresholds

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.reference_scale_multiplicand

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM curated.reference_study_scales

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.main_qs

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.main_lr10

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_history_annotation

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_lead

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_lead_study_assignment

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_question

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_rater

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_remediation

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_review_item_response

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_scale_review_form

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_scale_review_form_review

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_score_change_query

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_score_change_request

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_study

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM transformed.carp_review
