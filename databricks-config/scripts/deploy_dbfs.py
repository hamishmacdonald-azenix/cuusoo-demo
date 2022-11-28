from databricks_cli.dbfs.api import *
import os 
import json  
from databricks_cli.sdk import ApiClient 
import click

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_dbfs(config_file:str="config.json")->None:    
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config["dbfs"] is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        dbfsApi = DbfsApi(dbClient)

        for dbfs in config["dbfs"]:
            print(f"uploading {dbfs['source_path']} to {dbfs['target_path']}")
            dbfsApi.cp(
                src=dbfs["source_path"], 
                dst=dbfs["target_path"],
                recursive=dbfs["recursive"],
                overwrite=dbfs["overwrite"]
            )
            print(f"uploaded {dbfs['source_path']} to {dbfs['target_path']}\n")
            
if __name__ == "__main__":
    deploy_dbfs()