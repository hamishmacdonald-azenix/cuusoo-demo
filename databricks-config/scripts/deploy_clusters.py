import os 
import json 
import databricks_cli.sdk.service as services 
from databricks_cli.sdk import ApiClient 
import click

def get_cluster(clusterObjectList:list, cluster_name:str)->str:
    """
    Helper function to get cluster object from a list of clusters 
    """
    for cluster in clusterObjectList:
        if cluster["cluster_name"] == cluster_name: 
            return cluster
    raise Exception(f"Cluster {cluster_name} could not be found.")

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_clusters(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    clusters = config.get("clusters")
    if clusters is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        # cluster service operations 
        clusterService = services.ClusterService(dbClient)

        # cluster policy operations
        # Get the policy ID based on the policy name in the config file
        policyService = services.PolicyService(dbClient)

        for cluster in clusters:
            clusterObjectList = clusterService.list_clusters().get("clusters")
            try:
                cluster_name_list = [cluster["cluster_name"] for cluster in clusterObjectList]
            except:
                cluster_name_list = []
            try:
                policy_id = [policy["policy_id"] for policy in policyService.list_policies().get("policies") if cluster["policy_id"] == policy["name"]]
            except:
                policy_id = []
            if policy_id != []:
                cluster["policy_id"] = policy_id[0]
            # check if cluster exists 
            if cluster["cluster_name"] in cluster_name_list: 
                availCluster = get_cluster(clusterObjectList=clusterObjectList, cluster_name=cluster["cluster_name"])
                # update cluster 
                print(f"cluster `{availCluster['cluster_name']}` already exists with id `{availCluster['cluster_id']}`")
                print(f"proceeding with updating config for `{availCluster['cluster_name']}`")
                cluster["cluster_id"] = availCluster["cluster_id"]
                # CLI does not currently support init scripts and policy id so calling the API directly
                dbClient.perform_query(method="POST", path="/clusters/edit", data=cluster)
                print(f"cluster `{availCluster['cluster_name']}` has been updated")
                # Pin the cluster
                clusterService.pin_cluster(cluster_id=cluster["cluster_id"])
                print(f"cluster `{availCluster['cluster_name']}` has been pinned")
            else: 
                # create cluster 
                # CLI does not currently support init scripts and policy id so calling the API directly
                response = dbClient.perform_query(method="POST", path="/clusters/create", data=cluster)
                print(f"cluster has been created with id: {response['cluster_id']}")
                # Pin the cluster
                clusterService.pin_cluster(cluster_id=response['cluster_id'])
                print(f"cluster with id: {response['cluster_id']} has been pinned")

if __name__ == "__main__":
    deploy_clusters()