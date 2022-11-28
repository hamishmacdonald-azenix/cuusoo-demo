from databricks_cli.workspace.api import *
import os 
import json  
from databricks_cli.sdk import ApiClient 
import click

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_dir(config_file:str="config.json")->None:    
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config.get("directories") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        workspaceApi = WorkspaceApi(dbClient)

        for directory in config.get("directories"):
            if directory["target_path"][:1] != "/": # target_path must contain "/" at the start 
                directory["target_path"] = f'/{directory["target_path"]}'
            print(f"uploading {directory['source_path']} to {directory['target_path']}")
            workspaceApi.import_workspace_dir(
                source_path=directory["source_path"], 
                target_path=directory["target_path"],
                overwrite=directory["overwrite"],
                exclude_hidden_files=directory["exclude_hidden_files"]
            )
            print(f"uploaded {directory['source_path']} to {directory['target_path']}\n")
            
            
if __name__ == "__main__":
    deploy_dir()