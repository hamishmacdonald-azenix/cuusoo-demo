import os 
import json  
from databricks_cli.sdk import ApiClient 
from cuusoo_databricks_api.permissions.api import PermissionsClustersService
import databricks_cli.sdk.service as services 
import click
from deploy_clusters import get_cluster

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_permissions_clusters(config_file:str="config.json")->None:    
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config.get("permissions_clusters") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        permissionsClustersService = PermissionsClustersService(dbClient)
        clusterService = services.ClusterService(dbClient)
        existing_clusters = clusterService.list_clusters().get("clusters")

        for permission_cluster in config.get("permissions_clusters"):
            print(f"updating permissions for {permission_cluster['cluster_name']}")
            cluster_id = get_cluster(existing_clusters, permission_cluster["cluster_name"])["cluster_id"]
            permission_cluster_updated = permissionsClustersService.replace_permissions(cluster_id=cluster_id,data={"access_control_list":permission_cluster["access_control_list"]})
            print(f"permissions for {permission_cluster['cluster_name']} has been updated")
            
if __name__ == "__main__":
    deploy_permissions_clusters()