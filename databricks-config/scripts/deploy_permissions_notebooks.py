import os 
import json  
from databricks_cli.sdk import ApiClient 
from cuusoo_databricks_api.permissions.api import PermissionsNotebooksService
import databricks_cli.sdk.service as services 
import click

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_permissions_directories(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    
    with open(config_file) as f: 
        config = json.load(f)
    if config.get("permissions_notebooks") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        permissionsNotebooksService = PermissionsNotebooksService(dbClient)
        workspaceService = services.WorkspaceService(dbClient)
            
        for permission_notebook in config.get("permissions_notebooks"): 
            workspace_object = workspaceService.get_status(path=permission_notebook["notebook_name"])
            notebook_id = workspace_object.get("object_id")
            object_type = workspace_object.get("object_type")
            if notebook_id is not None and object_type=="NOTEBOOK": 
                # notebook exists 
                print(f"updating permissions for notebook: {permission_notebook['notebook_name']}")
                permission_notebook_updated = permissionsNotebooksService.replace_permissions(
                    notebook_id=notebook_id,
                    data={"access_control_list":permission_notebook["access_control_list"]}
                )
                print(f"permissions for directory: {permission_notebook['notebook_name']} has been updated")

if __name__ == "__main__":
    deploy_permissions_directories()