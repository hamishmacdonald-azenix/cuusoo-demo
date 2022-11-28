
class SqlEndpointsService():
    """
    API for interacting with Databricks SQL Endpoint APIs: https://docs.databricks.com/sql/api/sql-endpoints.html
    """
    def __init__(self, client):
        self.client = client 

    def get_endpoints(self, headers=None):
        """
        Get a list of all available endpoints 
        """
        return self.client.perform_query("GET", f"/sql/endpoints/", headers=headers)

    def get_endpoint(self, endpoint_id:str, headers=None):
        """
        Gets a specific endpoint based on the endpoint id 
        """
        return self.client.perform_query("GET", f"/sql/endpoints/{endpoint_id}", headers=headers)

    def create_endpoint(self, data:dict, headers=None):
        """
        Creates an endpoint according to specifications provided by Databricks: https://docs.databricks.com/sql/api/sql-endpoints.html#create
        """
        return self.client.perform_query("POST", f"/sql/endpoints",data=data, headers=headers)

    def edit_endpoint(self, endpoint_id:str, data:dict, headers=None):
        """
        Edits an endpoint based on the specified endpoint id, in accordance to specifications provided by Databricks: https://docs.databricks.com/sql/api/sql-endpoints.html#edit
        """
        data["id"] = endpoint_id # add key-value pair for id 
        return self.client.perform_query("POST", f"/sql/endpoints/{endpoint_id}/edit",data=data, headers=headers)

    def delete_endpoint(self, endpoint_id:str, headers=None):
        """
        Deletes an endpoint based on the specified endpoint id
        """
        return self.client.perform_query("DELETE", f"/sql/endpoints/{endpoint_id}",headers=headers)