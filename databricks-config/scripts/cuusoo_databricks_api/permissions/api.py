class PermissionsClustersService():
    """
    API for managing cluster permissions
    """
    def __init__(self, client):
        """
        Provide API Client to initialise 
        """
        self.client = client 

    def get_permissions(self, cluster_id:str="", headers=None):
        return self.client.perform_query("GET", f"/preview/permissions/clusters/{cluster_id}", headers=headers)

    def replace_permissions(self, cluster_id:str="", data:dict=None, headers=None):
        return self.client.perform_query("PUT", f"/preview/permissions/clusters/{cluster_id}", data=data, headers=headers)

class PermissionsSqlEndpointsService():
    """
    API for managing sql endpoints permissions
    """
    def __init__(self, client):
        """
        Provide API Client to initialise 
        """
        self.client = client 

    def get_permissions(self, endpoint_id:str="", headers=None):
        return self.client.perform_query("GET", f"/permissions/sql/endpoints/{endpoint_id}", headers=headers)

    def replace_permissions(self, endpoint_id:str="", data:dict=None, headers=None):
        return self.client.perform_query("PUT", f"/permissions/sql/endpoints/{endpoint_id}", data=data, headers=headers)

class PermissionsDirectoriesService():
    """
    API for managing directories permissions
    """
    def __init__(self, client):
        """
        Provide API Client to initialise 
        """
        self.client = client 

    def get_permissions(self, directory_id:str="", headers=None):
        return self.client.perform_query("GET", f"/preview/permissions/directories/{directory_id}", headers=headers)

    def replace_permissions(self, directory_id:str="", data:dict=None, headers=None):
        return self.client.perform_query("PUT", f"/preview/permissions/directories/{directory_id}", data=data, headers=headers)

class PermissionsNotebooksService():
    """
    API for managing notebooks permissions
    """
    def __init__(self, client):
        """
        Provide API Client to initialise 
        """
        self.client = client 

    def get_permissions(self, notebook_id:str="", headers=None):
        return self.client.perform_query("GET", f"/preview/permissions/notebooks/{notebook_id}", headers=headers)

    def replace_permissions(self, notebook_id:str="", data:dict=None, headers=None):
        return self.client.perform_query("PUT", f"/preview/permissions/notebooks/{notebook_id}", data=data, headers=headers)