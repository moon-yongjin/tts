import requests
import json
import sys

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
POD_ID = "4j0uvlhn1s17wd"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

query = """
query {
  myself {
    pods {
      id
      name
      runtime {
        uptimeInSeconds
        ports {
          ip
          privatePort
          publicPort
          type
        }
      }
    }
  }
}
"""

def main():
    response = requests.post(url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        pods = data.get('data', {}).get('myself', {}).get('pods', [])
        if pods:
            for pod in pods:
                print(f"ID: {pod['id']}, Name: {pod['name']}")
                print(json.dumps(pod, indent=2))
                print("-" * 50)
        else:
            print("No pods found.")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
