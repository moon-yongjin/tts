import requests
import json

token = "AQ.Ab8RN6LtqRkms6yuPcW90pwuEcJhN5O9mlAFfgfKb93NMTrPHg"

print("🔍 Testing token as Adobe Firefly / Generic REST token...")

# 1. Adobe Firefly Test
firefly_url = "https://firefly-api.adobe.io/v2/images/generate"
headers = {
    "Authorization": f"Bearer {token}",
    "X-Api-Key": "YOUR_CLIENT_ID", # Usually needs a client ID too
    "Content-Type": "application/json"
}

try:
    # Just a probe
    response = requests.get("https://ims-na1.adobelogin.com/ims/validate_token/v1", params={"token": token, "client_id": "none"})
    print(f"📡 Adobe IMS Probe: {response.status_code}")
    print(f"📝 Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Adobe Probe Error: {e}")

# 2. Google Cloud / Vertex AI Test (Access Token probe)
vertex_url = "https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1/publishers/google/models/imagen-3.0-generate:predict"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    response = requests.get("https://www.googleapis.com/oauth2/v1/tokeninfo", params={"access_token": token})
    print(f"📡 Google Token Info Probe: {response.status_code}")
    print(f"📝 Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Google Probe Error: {e}")
