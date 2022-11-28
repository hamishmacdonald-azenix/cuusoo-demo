import os 
import json  
from databricks_cli.sdk import ApiClient 
from cuusoo_databricks_api.users.api import UsersService
import click

@click.command()
@click.option("--config_file", default="config.json", help="The path to your environment's config file, e.g. config.dev.json")
@click.option("--delete_users", default=False, is_flag=True)
def deploy_users(config_file:str="config.json", delete_users:bool=False)->None:
    def get_user_id(dbrUsersResources:list, username:str)->str:
        """
        inputs: 
        - dbrUsersResources: list of databricks user resources 
        - username: username to search for 
        
        returns: 
        - user id: id of the user found in dbrUserResources
        """
        for user in dbrUsersResources:
            if user["userName"] == username:
                return user["id"]

    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    with open(config_file) as f: 
        config = json.load(f)

    if config.get("users") is not None:
        # databricks client 
        dbClient = ApiClient(host=os.environ.get("DATABRICKS_HOST"), token=DATABRICKS_TOKEN)
        
        usersService = UsersService(dbClient)
        dbrUsers = usersService.get_users()
        existingUsers = [resource["userName"] for resource in dbrUsers.get("Resources")]

        for user in config.get("users"):
            if user["userName"] in existingUsers:
                # update user 
                print(f"user `{user['userName']}` already exists")
                # get user id 
                userId = get_user_id(dbrUsers.get("Resources"), user["userName"])
                updated_user = usersService.update_user(user_id=userId, data=user)
                print(f"user `{user['userName']}` with id `{userId}` has been updated\n")
            else: 
                # create user 
                print(f"creating new user `{user['userName']}`")
                new_user = usersService.create_user(data=user)
                print(f"user `{user['userName']}` with id `{new_user['id']}` has been created\n")

        # if delete_users: 
        #     usersToCreate = [user["userName"] for user in config.get("users")]
        #     for existingUser in existingUsers:
        #         if existingUser not in usersToCreate:
        #             userId = get_user_id(dbrUsers.get("Resources"), existingUser)
        #             print(f"deleting user `{existingUser}` with id `{userId}`")
        #             deleted_user = usersService.delete_user(user_id=userId)
        #             print(f"user `{existingUser}` with id `{userId}` has been deleted")

if __name__ == "__main__":
    deploy_users()