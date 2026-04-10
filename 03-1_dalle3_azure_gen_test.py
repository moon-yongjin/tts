import os
import json
import sys
from openai import AzureOpenAI

# 1. Configuration
CONFIG_PATH = "config.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found.")
        sys.exit(1)

def main():
    config = load_config()
    
    # 2. Extract Credentials (User said "Use that Azure Key")
    # We use the speech key because it's the only one we have.
    api_key = config.get("Azure_Speech_Key")
    api_version = "2024-02-01" # Standard for DALL-E 3
    
    # 3. Missing Endpoint Check
    # Azure OpenAI requires an endpoint. We don't have one in config.
    azure_endpoint = config.get("Azure_OpenAI_Endpoint", "https://REPLACE_WITH_YOUR_ENDPOINT.openai.azure.com/")
    
    print(f"🔑 Using API Key: {api_key[:5]}... (From 'Azure_Speech_Key')")
    print(f"🌐 Using Endpoint: {azure_endpoint}")
    
    if "REPLACE" in azure_endpoint:
        print("\n⚠️ [CRITICAL ERROR] Azure OpenAI Endpoint is MISSING!")
        print("   To use DALL-E 3, I need the endpoint URL (e.g., https://my-resource.openai.azure.com).")
        print("   The 'Azure_Speech_Key' is for TTS, but connection *might* work if the resource supports both (unlikely).")
        print("   Please provide the endpoint in config.json as 'Azure_OpenAI_Endpoint'.")
        sys.exit(1)
        
    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        api_key=api_key,
    )

    # 4. Prompt from Script
    prompt = "A 72-year-old Korean woman with a cold, determined expression, showing a recording device to her shocked son and daughter-in-law in a messy living room. Cinematic lighting, dramatic atmosphere, high resolution, realistic style."
    
    print(f"🎨 Generating Image with Prompt: {prompt[:50]}...")

    try:
        result = client.images.generate(
            model="dall-e-3", # Deployment name must match this or be provided
            prompt=prompt,
            n=1
        )

        image_url = result.data[0].url
        print(f"✅ Image Generated: {image_url}")
        
    except Exception as e:
        print(f"\n❌ Generation Failed: {e}")
        print("   (Likely causes: Invalid Key, Wrong Endpoint, or Deployment Name mismatch)")

if __name__ == "__main__":
    main()
