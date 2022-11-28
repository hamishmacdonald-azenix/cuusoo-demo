import requests
import json, os

databricks_token = os.environ.get('token')
databricks_url = os.environ.get('databricks_url')
repo_id = os.environ.get('repo_id')

url = f"{databricks_url}/api/2.0/repos/{repo_id}"

payload = json.dumps({
  "branch": "master"
})
headers = {
  'Authorization': f'Bearer {databricks_token}',
  'Content-Type': 'application/json'
}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)
