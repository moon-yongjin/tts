import requests
import json
import os
import base64

DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = "/Users/a12/Downloads/Script_Scenes_Dynamic/Settings_Test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_settings(name, payload):
    print(f"🧪 Testing: {name}...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"💾 Saved: {filepath}")
            else:
                print(f"⚠️ No images in response for {name}: {data.keys()}")
        else:
            print(f"❌ Error {name}: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"🔥 Exception {name}: {e}")

prompt = "Early 1980s film photo, a sophisticated Korean woman in her 50s, elegant emerald green silk dress, sharp almond eyes, looking at mirror, realistic skin texture, 35mm film grain, sharp focus, detailed face."

tests = [
    ("1024_EulerATrailing_Steps6", {
        "prompt": prompt,
        "steps": 6,
        "sampler": "Euler A Trailing",
        "width": 1024,
        "height": 1024,
        "guidance_scale": 1.0
    }),
    ("1024_2MTrailing_Steps6", {
        "prompt": prompt,
        "steps": 6,
        "sampler": "DPM++ 2M Trailing",
        "width": 1024,
        "height": 1024,
        "guidance_scale": 1.0
    }),
    ("1024_DDIMTrailing_Steps10", {
        "prompt": prompt,
        "steps": 10,
        "sampler": "DDIM Trailing",
        "width": 1024,
        "height": 1024,
        "guidance_scale": 1.0,
        "sharpness": 10
    })
]

for name, payload in tests:
    test_settings(name, payload)
