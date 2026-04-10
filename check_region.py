import requests
import json

API_KEY = "rpa_FHG3CVKINI8UZ0II8UU0V4O482A57CBUCMZDLU261yr9lz"

url = "https://api.runpod.io/graphql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def get_region():
    # 최대한 많은 정보를 가져와서 지역을 유추합니다.
    query = """
    query {
      myself {
        pods {
          id
          name
          dataCenterId
          regionId
          runtime {
            ports {
              ip
            }
          }
        }
      }
    }
    """
    try:
        response = requests.post(url, json={'query': query}, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(json.dumps(get_region(), indent=2))
