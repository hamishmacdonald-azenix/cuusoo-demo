import os 
import json 
import databricks_cli.sdk.service as services 
from databricks_cli.sdk import ApiClient 
import click

def get_cluster_policies(policyObjectList:list, policy_name:str)->str:
    """
    Helper function to get policy object from a list of policies 
    """
    for policy in policyObjectList:
        if policy["name"] == policy_name: 
            return policy
    raise Exception(f"Policy {policy_name} could not be found.")

def replace_cluster_policy_vars(policy_name:str, replace_policy_config:str)->str:
    """
    Helper function to replace the placaeholder values in the policy file
    """
    try:
        with open(f"../policies/{policy_name}.json") as f: 
            policy_config = json.load(f)
            for config in policy_config:
                for replace_config in replace_policy_config:
                    if config == replace_config.split(":")[0]:
                        policy_config[replace_config.split(":")[0]][replace_config.split(":")[-1]] = replace_policy_config[replace_config]
            # Make the response valid json
            response = str(policy_config).replace("'", '\"').replace('True', 'true').replace('False', 'false')
            return(response)
    except:
        raise Exception(f"Policy configuration for policy {policy_name} cannot be replaced.")

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_cluster_policies(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    policies = config.get("cluster_policies")
    if policies is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        # policy service operations 
        policyService = services.PolicyService(dbClient)

        for policy in policies:
            policyObjectList = policyService.list_policies().get("policies")
            try:
                policy_name_list = [policy["name"] for policy in policyObjectList]
            except:
                policy_name_list = []
            # replace the required config in the policy definition
            policy["definition"] = replace_cluster_policy_vars(policy_name=policy["policy_name"], replace_policy_config=policy["policy_config"])
            # check if policy exists 
            policy_name_list
            if policy["policy_name"] in policy_name_list: 
                availpolicy = get_cluster_policies(policyObjectList=policyObjectList, policy_name=policy["policy_name"])
                # update policy 
                print(f"Cluster policy `{availpolicy['name']}` already exists with id `{availpolicy['policy_id']}`")
                print(f"proceeding with updating config for `{availpolicy['name']}`")
                policy["policy_id"] = availpolicy["policy_id"]
                # There is a bug in the Databricks CLI so call the API directly
                dbClient.perform_query(method="POST", path="/policies/clusters/edit", data={"policy_id": availpolicy["policy_id"], "name": availpolicy['name'], "definition": policy["definition"]})
                # policyService.edit_policy(policy_id=availpolicy["policy_id"], policy_name=availpolicy['name'], definition=policy["definition"])
                print(f"Cluster policy `{availpolicy['name']}` has been updated")
            else: 
                # create policy 
                # There is a bug in the Databricks CLI so call the API directly
                response = dbClient.perform_query(method="POST", path="/policies/clusters/create", data={"name": policy["policy_name"], "definition": policy["definition"]})
                # response = policyService.create_policy(policy_name=policy["policy_name"], definition=policy["definition"])
                print(f"Cluster policy has been created with id: {response['policy_id']}")

if __name__ == "__main__":
    deploy_cluster_policies()