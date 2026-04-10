import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SUPERTONE_API_KEY")

endpoints = [
    "https://api.supertoneapi.com/v1/voices",
    "https://api.supertone.ai/v1/voices"
]

headers = {
    "x-sup-api-key": API_KEY,
}

for url in endpoints:
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Successfully retrieved voices!")
            # print(response.json())
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
