config_file=$1
. ./get_databricks_pat.sh $config_file $2
# python3 deploy_cluster_policies.py --config_file $config_file
python3 deploy_dbfs.py --config_file $config_file
python3 deploy_clusters.py --config_file $config_file
# python3 deploy_permissions_clusters.py --config_file $config_file
python3 deploy_sql_endpoints.py --config_file $config_file
python3 deploy_jobs.py --config_file $config_file