import requests
import json

api_key = "54567210-a9eda8229603b48ff202cbd7b"
url = f"https://pixabay.com/api/?key={api_key}&q=nature&image_type=photo"

print(f"Testing Pixabay API Key: {api_key[:8]}...")

try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Total hits: {data.get('totalHits')}")
    else:
        print(f"❌ Failed! Status Code: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
