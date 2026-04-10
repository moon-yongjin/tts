from google import genai
import os
import json

CONFIG_PATH = "/Users/a12/projects/tts/config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    api_key = config.get("Gemini_API_KEY")

client = genai.Client(api_key=api_key)

try:
    model_name = 'gemini-2.0-flash'
    print(f"Testing {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents="Hello, say 'OK' if you can read this."
    )
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with {model_name}: {e}")

try:
    model_name = 'models/gemini-2.0-flash'
    print(f"\nTesting {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents="Hello, say 'OK' if you can read this."
    )
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with {model_name}: {e}")
