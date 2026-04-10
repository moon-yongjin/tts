import requests
import json
import sys

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"
POD_ID = "ffwf9h8ir0mzs6"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def get_status(pid=None):
    target_id = pid if pid else POD_ID
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
    response = requests.post(url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        pods = data.get('data', {}).get('myself', {}).get('pods', [])
        for pod in pods:
            if pod['id'] == target_id:
                return pod
        return None
    return f"Error: {response.status_code}"

def edit_pod(gpu_type_id):
    # Experimental: Attempting to edit pod to assign a GPU
    mutation = """
    mutation ($input: PodEditJobInput!) {
      podEditJob(input: $input) {
        id
      }
    }
    """
    variables = {
        "input": {
            "podId": POD_ID,
            "gpuTypeId": gpu_type_id
        }
    }
    response = requests.post(url, json={'query': mutation, 'variables': variables}, headers=headers)
    return response.json()

def start_pod():
    mutation = """
    mutation {
      podResume(input: {
        podId: "%s"
      }) {
        id
        desiredStatus
      }
    }
    """ % POD_ID
    response = requests.post(url, json={'query': mutation}, headers=headers)
    return response.json()

def stop_pod():
    stop_mutation = """
    mutation {
      podStop(input: {
        podId: "%s"
      }) {
        id
        desiredStatus
      }
    }
    """ % POD_ID
    response = requests.post(url, json={'query': stop_mutation}, headers=headers)
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_runpod.py [status|start|stop|edit] [gpu_type_id]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "status":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_status(pid), indent=2))
    elif cmd == "start":
        print(json.dumps(start_pod(), indent=2))
    elif cmd == "stop":
        print(json.dumps(stop_pod(), indent=2))
    elif cmd == "edit":
        if len(sys.argv) < 3:
            print("Please specify gpu_type_id (e.g., 'NVIDIA GeForce RTX 3090')")
            sys.exit(1)
        gpu_id = sys.argv[2]
        print(json.dumps(edit_pod(gpu_id), indent=2))
