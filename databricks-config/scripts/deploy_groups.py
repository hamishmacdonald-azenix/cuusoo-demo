import os 
import json  
from databricks_cli.sdk import ApiClient 
import databricks_cli.sdk.service as services 
import click
        
def set_members(groupsService:services.GroupsService, group_name:str, members:list)->None:
    """
    This is a helper function used to create, update and remove users/groups from parent groups. 

    Parameters: 
    - groupsService: the group service object 
    - group_name: the name of a group that exists 
    - members: the list of members specified in the config file e.g. [{"type":"user", "name":"hello-world@cuusoo.com.au"}]
    """
    group_members = groupsService.get_group_members(group_name=group_name).get("members")
    # add or update members 
    for member in members: 
        if member["type"].lower() == "user":
            user = groupsService.add_to_group(parent_name=group_name, user_name=member["name"])
            print(f"user {member['name']} has been added to group `{group_name}`")
        elif member["type"].lower() == "group":
            group = groupsService.add_to_group(parent_name=group_name, group_name=member["name"])
            print(f"group {member['name']} has been added to parent group `{group_name}`")
        else: 
            raise Exception("Please choose a member type of either ['user', 'group]")
    # remove members 
    members_to_create = [member["name"] for member in members]
    if group_members is not None: 
        for existing_member in group_members:
            if existing_member.get("user_name") is not None and existing_member.get("user_name") not in members_to_create:
                print(f"removing user {existing_member.get('user_name')} from group `{group_name}`")
                groupsService.remove_from_group(parent_name=group_name,user_name=existing_member.get("user_name"))
                print(f"user {existing_member.get('user_name')} has been removed from group {group_name}")
            elif existing_member.get("group_name") is not None and existing_member.get("group_name") not in members_to_create:
                print(f"removing group {existing_member.get('group_name')} from parent group `{group_name}`")
                groupsService.remove_from_group(parent_name=group_name,group_name=existing_member.get("group_name"))
                print(f"group {existing_member.get('group_name')} has been removed from parent group `{group_name}`")

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
def deploy_groups(config_file:str="config.json")->None:
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config.get("groups") is not None: 
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        groupsService = services.GroupsService(dbClient)
        dbrGroups = groupsService.get_groups()
        
        for group in config.get("groups"):
            if group["group_name"] in dbrGroups.get("group_names"):
                print(f"update group {group['group_name']}")
                set_members(groupsService=groupsService, group_name=group["group_name"], members=group["members"])
            else: 
                # create group
                print(f"create new group `{group['group_name']}`")
                new_group = groupsService.create_group(group_name=group['group_name'])
                print(f"group `{group['group_name']}` has been created\n")
                set_members(groupsService=groupsService, group_name=group["group_name"], members=group["members"])

if __name__ == "__main__":
    deploy_groups()