import requests
import json
import time

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
POD_ID = "4j0uvlhn1s17wd"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

mutation = f"""
mutation {{
  podStart(input: {{ podId: "{POD_ID}" }}) {{
    id
    desiredStatus
  }}
}}
"""

def start_pod():
    print(f"🚀 Starting Pod {POD_ID}...")
    response = requests.post(url, json={'query': mutation}, headers=headers)
    if response.status_code == 200:
        print("✅ Start command sent!")
        print(response.json())
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    start_pod()
