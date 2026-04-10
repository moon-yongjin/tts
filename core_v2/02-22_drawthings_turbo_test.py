import os
import requests
import json
import base64
import time
from pathlib import Path

# Configuration
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_DIR = Path.home() / "Downloads"
# os.makedirs(OUTPUT_DIR, exist_ok=True) # Downloads already exists

# "PREMIUM CARE" Prompt with Natural HD adjustments
PROMPT = (
    "A natural close-up portrait of a 25-year-old Korean woman with authentic facial features, "
    "wearing a sophisticated professional navy blazer. She is standing in a sunlit modern luxury office. "
    "In her hand, she holds a sleek transparent glass tablet displaying the clear text 'PREMIUM CARE'. "
    "Soft cinematic lighting, Korean woman facial features, soft HD quality (720p), natural skin texture, "
    "gentle film grain, shot on 85mm lens."
)

def generate_turbo(prompt):
    filename = f"drawthings_turbo_{int(time.time())}.png"
    filepath = OUTPUT_DIR / filename
    
    print(f"🚀 [Draw Things TURBO] Generating: {filename}...")
    print(f"📝 Prompt: {prompt}")
    
    # HF Space (Official) Optimized Settings
    payload = {
        "prompt": prompt,
        "negative_prompt": "", # HF Space usually uses no negative prompt
        "steps": 9,        # Official HF Space recommendation
        "cfg_scale": 0.0,   # Official HF Space setting for Z-Image-Turbo
        "width": 720,
        "height": 1280,
        "sampler_name": "DPM++ 2M Karras",
        "seed": -1
    }

    start_time = time.time()
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                img_data = base64.b64decode(result["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                elapsed = time.time() - start_time
                print(f"✅ Success: {filepath}")
                print(f"⏱️ Turbo Generation Time: {elapsed:.2f} seconds")
                return str(filepath), elapsed
            else:
                print(f"❌ Error: No image data in response. Result: {result}")
        else:
            print(f"❌ API Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None, 0

if __name__ == "__main__":
    path, elapsed = generate_turbo(PROMPT)
    if path:
        print(f"\n🎉 Turbo Result saved to: {path}")
