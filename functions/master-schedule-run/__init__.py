import logging
import azure.functions as func
import os
import traceback
from azure.identity import DefaultAzureCredential
from croniter import croniter
from datetime import datetime
import common

def get_active_systems():
    """
    Get a list of all the tasks in the given system
    """
    systems = common.getSystemConfig(storage_url=storage_url, container_name=container, credential=default_credential)
    systems = [s for s in systems if s["enabled"] == True]
    results = common.parallel_run(get_system, systems)
    results = [r for r in results ]
    return results

def get_system(system):
    """
    Get the pipeline status for a given system
    """
    pipelineName = system["pipeline_name"]
    systemName = system["system_name"]

    # Get the latest pipeline run status
    pipeline_status = common.getPipelineLatestRunStatus(subscription_id=subscription_id, 
        resource_group_name=resource_group_name, 
        data_factory_name=data_factory_name, 
        system_name=systemName, 
        pipeline_name=pipelineName, 
        credential=default_credential)
    system["pipeline_status"] = pipeline_status
    return system

def get_databricks_info(system):
    """
    Apped the Databricks cluster ID to each system
    """
    cluster_name = ""
    system["databricks_cluster_id"] = ""
    if "databricks_cluster_name" in system:
        cluster_name = system["databricks_cluster_name"]
    if cluster_name != "":
        cluster_id = [cluster["cluster_id"] for cluster in databricks_cluster_list if cluster_name in cluster["cluster_name"]][0]
        system["databricks_cluster_id"] = cluster_id
    return system

def enrich_with_databricks_info(systems):
    """
    Add the Databricks cluster ID to the systems in parallel
    """
    results = common.parallel_run(get_databricks_info, systems)
    results = [r for r in results]
    return results

def get_task(system):
    """
    Get an individual task's details
    """
    # Get all the tasks to run for the given system
    tasks = common.getContainerBlobs(storage_url=storage_url, container_name=container, 
        credential=default_credential, name_starts_with=system["config_path"])
    task_list = [task for task in tasks]
    task_logs = [{"name": t.name, "creation_time": t.creation_time} for t in task_list if "/Log/" in t.name]
    return [{"task_name": t.name, "system": system, "task_logs": task_logs} for t in task_list if "/Log/" not in t.name]

def get_tasks(systems):
    """
    Get a list of all the tasks in the given system
    """
    results = common.parallel_run(get_task, systems, apply_flat_map=True)
    results = [r for r in results]
    return results

def get_task_config(task):
    """
    Get the task configuration for a given task
    """
    taskConfig = common.getTaskConfig(config_file_path=task["task_name"], 
        storage_url=storage_url, container_name=container, credential=default_credential)
    task["config"] = taskConfig
    return task

def enrich_with_config(tasks):
    """
    Add the config to the tasks in parallel
    """
    results = common.parallel_run(get_task_config, tasks)
    results = [x for x in results if x["config"]["enabled"] == True]
    return results

def get_log_details(task):
    """
    Get the task log for a given task   
    """
    configFilePath = task["system"]["config_path"]
    if configFilePath[-1] != "/":
        configFilePath += "/"
    # Get the latest log status for the task
    try:
        logStatus, logDate = common.getLogStatus(config_file_path=configFilePath, 
            config_file_name=task["task_name"].split("/")[-1], storage_url=storage_url, container_name=container, credential=default_credential, log_list=task["task_logs"])
        # Ensure all the dependencies have completed successsfully if there are any
        task["log_status"] = logStatus
        task["log_date"] = logDate
    except:
        print(f'Failed to read log file {configFilePath + task["task_name"].split("/")[-1]}')
        task["log_status"] = "Error"
        task["log_date"] = ""
    return task

def enrich_with_log_details(tasks):
    """
    Add the log details to the tasks in parallel
    """
    results = common.parallel_run(get_log_details, tasks)
    return results

def enrich_with_dependencies_status(tasks):
    """
    Check if all the task dependencies have completed
    """
    # No need for parallelism here, it is basically classic logic and not calling any APIs
    for task in tasks:
        task_config = task["config"]
        depend_succeeded = True
        if "dependencies" in task_config:
            dependencies = task_config["dependencies"]
            for dependency in dependencies:
                dependency_tasks = [x for x in tasks if x["task_name"] == dependency]
                if len(dependency_tasks) > 0:
                    if dependency_tasks[0]["log_status"] != "Completed":
                        depend_succeeded = False
                        break
        task["dependencies_succeeded"] = depend_succeeded
    return tasks

def get_system_pipeline_details(systems, tasks):
    """
    Check which tasks need to be run and return the systems with all their tasks
    """
    utc_now = datetime.utcnow()
    for system in systems:
        tasks_to_run = []
        system_type = system["system_type"]
        system_name = system["system_name"]
        system["run_pipeline"] = False
        pipeline_status = system["pipeline_status"]
        for task in tasks:
            if system_name == task["system"]["system_name"]:
                # Check if the task needs to be run based on the task status, run date, start date of the task, dependency execution and status of the running pipeline
                log_status = task["log_status"]
                log_date = task["log_date"]
                dependencies_succeeded = task["dependencies_succeeded"]
                task_config = task["config"]
                if "start_date" in task["config"]:
                    start_date = datetime.fromisoformat(task["config"]["start_date"])
                else:
                    start_date = datetime.fromisoformat("1900-01-01")
                if log_status != "None":
                    iteration = croniter(task_config["cron_schedule"], log_date)
                    nextRunDate = iteration.get_next(datetime).replace(tzinfo=None)
                else:
                    nextRunDate = datetime(1900, 1, 1)
                if ((log_status == "Completed" and pipeline_status != "InProgress" and nextRunDate < utc_now and start_date <= utc_now) or (log_status != "Completed" and pipeline_status != "InProgress" )) and dependencies_succeeded == True:
                    tasks_to_run.append({"task_path": task["task_name"]})
        if tasks_to_run:
            system["run_pipeline"] = True
            if "databricks_cluster_id" in system:
                system["pipeline_parameters"] = {"system_name": system_name, "task_json": tasks_to_run, "databricks_cluster_id": system["databricks_cluster_id"]}
            else:
                system["pipeline_parameters"] = {"system_name": system_name, "task_json": tasks_to_run}
    return [system for system in systems if system["run_pipeline"] == True]

def run_systems(systems_to_run):
    """
    Run all the pipelines in parallel
    """
    results = common.parallel_run(run_pipeline, systems_to_run)
    results = [r for r in results]
    return results

def run_pipeline(system):
    """
    Run the Azure Data Factory pipeline for the given system
    """
    pipelineRunID = common.newPipelineRun(subscription_id=subscription_id, resource_group_name=resource_group_name, 
        data_factory_name=data_factory_name, pipeline_name=system["pipeline_name"], parameters=system["pipeline_parameters"], credential=default_credential)
    return pipelineRunID

def process_systems():
    systems = get_active_systems()
    systems = enrich_with_databricks_info(systems)
    tasks = get_tasks(systems)
    tasks = enrich_with_config(tasks)
    tasks = enrich_with_log_details(tasks)
    tasks = enrich_with_dependencies_status(tasks)
    systems_to_run = get_system_pipeline_details(systems, tasks)
    pipeline_runs = run_systems(systems_to_run)
    return pipeline_runs

def main(timer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow()

    try:
        # Get all the required config from the app settings
        global subscription_id, resource_group_name, data_factory_name, storage_account_name, databricks_url, databricks_pat, storage_url, container, databricks_cluster_list, default_credential
        subscription_id = os.environ['SUBSCRIPTION_ID']
        resource_group_name = os.environ['RESOURCE_GROUP_NAME']
        data_factory_name = os.environ['DATA_FACTORY_NAME']
        storage_account_name = os.environ['STORAGE_ACCOUNT_GENERIC']
        databricks_url = f"https://{os.environ['DATABRICKS_WORKSPACE_URL']}"
        databricks_pat = os.environ['DATABRICKS_PAT']
        storage_url = f"https://{storage_account_name}.blob.core.windows.net"
        container = "config"

        # Get all the Databricks cluster information
        databricks_cluster_list = common.getDatabricksClusters(databricks_url=databricks_url, databricks_token=databricks_pat)
        # Get the MSI credential to access services using the MSI
        default_credential = DefaultAzureCredential()
        # Get the pipeline runs to execute
        pipeline_runs = process_systems()
        logging.info('master-schedule-run timer trigger function ran at %s', utc_timestamp)
        if pipeline_runs == []:
            logging.info('No new pipelines executed')
        else:
            logging.info(f'Executed pipeline runs {pipeline_runs}')
                
    except Exception:
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            traceback.format_exc(), status_code=400)