"""
Users SCIM REST API Documentation: https://docs.databricks.com/dev-tools/api/latest/scim/scim-users.html
"""

class UsersService():
    def __init__(self, client):
        self.client = client 

    def get_users(self, headers=None):
        return self.client.perform_query('GET', '/preview/scim/v2/Users', headers=headers)

    def get_user(self, user_id:str="", headers=None):
        return self.client.perform_query('GET', f'/preview/scim/v2/Users/{user_id}', headers=headers)
    
    def create_user(self, data=None, headers=None):
        if headers==None:
            headers = {
                "Content-type": "application/scim+json"
            }
        return self.client.perform_query('POST', '/preview/scim/v2/Users', data=data, headers=headers)

    def update_user(self, user_id:str="", data=None, headers=None):
        if headers==None:
            headers = {
                "Content-type": "application/scim+json"
            }
        return self.client.perform_query('PUT', f'/preview/scim/v2/Users/{user_id}', data=data, headers=headers)

    def delete_user(self, user_id:str="", headers=None):
        return self.client.perform_query('DELETE', f'/preview/scim/v2/Users/{user_id}', headers=headers)