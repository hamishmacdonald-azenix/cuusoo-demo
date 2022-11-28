import os 
import json 
import databricks_cli.sdk.service as services 
from databricks_cli.sdk import ApiClient 
import click
import traceback

def get_job_by_name(jobObjectList:list, job_name:str)->str:
    """
    Helper function to get job object from a list of jobs 
    """
    for job in jobObjectList:
        if job["settings"]["name"] == job_name: 
            return job
    raise Exception(f"Job {job_name} could not be found.")

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_jobs(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    jobs = config["jobs"]
    if jobs is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN, jobs_api_version="2.1")
        
        # job service operations 
        jobService = services.JobsService(dbClient)

        # cluster service operations 
        clusterService = services.ClusterService(dbClient)

        for job in jobs:
            jobObjectList = jobService.list_jobs()
            if "jobs" in jobObjectList:
                jobObjectList = jobObjectList["jobs"]
            jobName = job["name"]
            # Get the cluster ID if required and replace the placeholder in the config file
            try:
                cluster_id = [cluster["cluster_id"] for cluster in clusterService.list_clusters().get("clusters") if cluster["cluster_name"] == job["cluster_name"]][0]
                taskItem = 0
                for task in job["tasks"]:
                    if not "job_cluster_key" in job["tasks"][taskItem] and not "existing_cluster_id" in job["tasks"][taskItem]:
                        job["tasks"][taskItem]["existing_cluster_id"] = cluster_id
                    taskItem += 1
                del job["cluster_name"]
            except Exception:
                cluster_id = None
            try:
                job_name_list = [job["settings"]["name"] for job in jobObjectList]
            except:
                job_name_list = []
            # Check if job exists 
            if jobName in job_name_list: 
                availjob = get_job_by_name(jobObjectList=jobObjectList, job_name=jobName)
                # Update job 
                print(f"job `{jobName}` already exists with id `{availjob['job_id']}`")
                print(f"proceeding with updating config for `{jobName}`")
                # Call the API directly
                dbClient.perform_query(method="POST", path="/jobs/reset", data={"job_id": availjob["job_id"], "new_settings": job})
                print(f"Job `{jobName}` has been updated")
            else: 
                # Create job 
                # Call the API directly
                response = dbClient.perform_query(method="POST", path="/jobs/create", data=job)
                print(f"Job has been created with id: {response['job_id']}")

if __name__ == "__main__":
    deploy_jobs()