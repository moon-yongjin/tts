import requests
import json

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
POD_ID = "4j0uvlhn1s17wd"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Try multiple possible log fields or methods to get logs
query = f"""
query {{
  pod(input: {{ podId: "{POD_ID}" }}) {{
    id
    name
    runtime {{
      uptimeInSeconds
    }}
  }}
}}
"""
# Note: In RunPod GraphQL, logs are often retrieved via podLogs(input: {podId: "..."})
query_logs = f"""
query {{
  podLogs(input: {{ podId: "{POD_ID}" }}) {{
    logs
  }}
}}
"""

def main():
    print("--- Fetching Pod Logs ---")
    response = requests.post(url, json={'query': query_logs}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
             print(f"Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            logs = data.get('data', {}).get('podLogs', {}).get('logs', "")
            print(logs)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
