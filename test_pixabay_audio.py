import requests

api_key = "54567210-a9eda8229603b48ff202cbd7b"
# Testing various guessed endpoints for music/sfx
endpoints = ["music", "sound-effects"]

for ep in endpoints:
    url = f"https://pixabay.com/api/{ep}/?key={api_key}&q=nature"
    print(f"Testing endpoint: {ep}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ Success on {ep}!")
            # print(response.json())
        else:
            print(f"❌ Failed on {ep}! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error on {ep}: {e}")
