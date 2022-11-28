import math
import os 
import json 
import databricks_cli.sdk.service as services 
from databricks_cli.sdk import ApiClient 
import click
import time
from datetime import datetime

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_cluster_libraries(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    clusters = config.get("cluster_libraries")
    if clusters is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        # cluster service operations
        clusterService = services.ClusterService(dbClient)

        # library service operations 
        libraryService = services.ManagedLibraryService(dbClient)
        
        for cluster in clusters:
            # Check the cluster state to see if it should be started
            cluster_details = [(_cluster["cluster_id"], _cluster["state"]) for _cluster in clusterService.list_clusters().get("clusters") if _cluster["cluster_name"] == cluster["cluster_name"]]
            cluster_id = cluster_details[0][0]
            cluster_state = cluster_details[0][1]
            run_start_date = datetime.utcnow()
            if cluster_state == "TERMINATED":
                clusterService.start_cluster(cluster_id=cluster_id)
                print(f"Cluster {cluster_id} is not started - Waiting for 60 seconds")
                time.sleep(60)
            # Keep checking until the status is RUNNING
            cluster_state = clusterService.get_cluster(cluster_id=cluster_id).get("state")
            while cluster_state == "PENDING" or cluster_state == "TERMINATING":
                # Make sure we haven't waited more than 10 minutes to start the cluster, otherwise there is a problem
                wait_time = math.floor((datetime.utcnow() - run_start_date).total_seconds() / 60)
                if wait_time >= 10:
                    print(f"Waited for more than 10 minutes for cluster {cluster_id} to start - Please check the cluster logs")
                    break
                print(f"Cluster {cluster_id} is not started - Waiting for 60 seconds. Total wait time is {wait_time} minutes")
                time.sleep(60)
                cluster_state = clusterService.get_cluster(cluster_id=cluster_id).get("state")
            # Install the libraries
            libraryService.install_libraries(cluster_id=cluster_id, libraries=cluster["libraries"])
            print(f"Libraries for cluster {cluster_id} successfully installed")

if __name__ == "__main__":
    deploy_cluster_libraries()