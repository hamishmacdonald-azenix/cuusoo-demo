import os 
import json  
from databricks_cli.sdk import ApiClient
from cuusoo_databricks_api import sql_endpoints 
from cuusoo_databricks_api.permissions.api import PermissionsSqlEndpointsService
from cuusoo_databricks_api.sql_endpoints.api import SqlEndpointsService
import click
from deploy_sql_endpoints import get_sql_endpoint

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_permissions_sql_endpoints(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config.get("permissions_sql_endpoints") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        permissionsSqlEndpointsService = PermissionsSqlEndpointsService(dbClient)
        sqlEndpointsService = SqlEndpointsService(dbClient)
        existing_sql_endpoints = sqlEndpointsService.get_endpoints().get("endpoints")

        for sql_endpoint in config.get("permissions_sql_endpoints"):
            print(f"updating permissions for {sql_endpoint['sql_endpoint_name']}")
            sql_endpoint_id = get_sql_endpoint(existing_sql_endpoints, sql_endpoint["sql_endpoint_name"])["id"]
            permission_sql_endpoint_updated = permissionsSqlEndpointsService.replace_permissions(endpoint_id=sql_endpoint_id,data={"access_control_list":sql_endpoint["access_control_list"]})
            print(f"permissions for {sql_endpoint['sql_endpoint_name']} has been updated")
            
if __name__ == "__main__":
    deploy_permissions_sql_endpoints()