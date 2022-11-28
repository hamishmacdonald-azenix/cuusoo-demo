import os 
import json  
from databricks_cli.sdk import ApiClient 
from cuusoo_databricks_api.permissions.api import PermissionsDirectoriesService
import databricks_cli.sdk.service as services 
import click

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_permissions_directories(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    
    with open(config_file) as f: 
        config = json.load(f)
    if config.get("permissions_directories") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        permissionsDirectoriesService = PermissionsDirectoriesService(dbClient)
        workspaceService = services.WorkspaceService(dbClient)

        for permission_directory in config.get("permissions_directories"): 
            workspace_object = workspaceService.get_status(path=permission_directory["directory_name"])
            directory_id = workspace_object.get("object_id")
            object_type = workspace_object.get("object_type")
            if directory_id is not None and object_type=="DIRECTORY": 
                # directory exists 
                print(f"updating permissions for directory: {permission_directory['directory_name']}")
                permission_directory_updated = permissionsDirectoriesService.replace_permissions(
                    directory_id=directory_id,
                    data={"access_control_list":permission_directory["access_control_list"]}
                )
                print(f"permissions for directory: {permission_directory['directory_name']} has been updated")

if __name__ == "__main__":
    deploy_permissions_directories()