import os 
import json 
from cuusoo_databricks_api.sql_endpoints.api import SqlEndpointsService
from databricks_cli.sdk import ApiClient 
import click

def get_sql_endpoint(sql_endpoint_list:list, sql_endpoint_name:str)->str:
    """
    Helper function to get sql endpoint object from a list of endpoints 
    """
    for endpoint in sql_endpoint_list:
        if endpoint["name"] == sql_endpoint_name: 
            return endpoint
    raise Exception(f"SQL endpoint {sql_endpoint_name} could not be found.")

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_sql_endpoints(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    sql_endpoints = config.get("sql_endpoints")
    if sql_endpoints is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        # cluster service operations 
        sqlEndpointsService = SqlEndpointsService(dbClient)

        for sql_endpoint in sql_endpoints:
            sql_endpoint_list = sqlEndpointsService.get_endpoints().get("endpoints")
            try:
                sql_endpoint_name_list = [endpoint["name"] for endpoint in sql_endpoint_list]
            except:
                sql_endpoint_name_list = []
            
            # check if endpoint exists 
            if sql_endpoint["name"] not in sql_endpoint_name_list: 
                # create 
                print(f"sql endpoint `{sql_endpoint['name']}` does not exist. creating now.")
                new_endpoint = sqlEndpointsService.create_endpoint(data=sql_endpoint)
                print(f"sql endpoint `{sql_endpoint['name']}` has been created.")
            else: 
                # update 
                existing_sql_endpoint = get_sql_endpoint(sql_endpoint_list=sql_endpoint_list, sql_endpoint_name=sql_endpoint['name'])
                print(f"sql endpoint `{sql_endpoint['name']}` already exists with id `{existing_sql_endpoint['id']}`. performing update.")
                updated_endpoint = sqlEndpointsService.edit_endpoint(endpoint_id=existing_sql_endpoint['id'], data=sql_endpoint)
                print(f"sql endpoint `{sql_endpoint['name']}` with id `{existing_sql_endpoint['id']}` has been updated.")

if __name__ == "__main__":
    deploy_sql_endpoints()