import os
import requests
import base64
import time

SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Manual_Test")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# User Request Prompt
USER_PROMPT = "Full body shot of a tall Korean woman standing on an athletic track, wearing running shoes, lean and toned physique, fair skin, natural sunlight, 8k raw photo, sharp focus"
STYLE_PROMPT = "Photorealistic, 8k RAW photo, Fujifilm XT4, Cinematic Lighting, Skin texture detail, Weathered face, Hyper-realistic eyes, Subtle cinematic grain, film grain, high ISO, natural imperfections, skin pores, raw photo, <lora:flux-RealismLora:0.8>"

full_prompt = f"{STYLE_PROMPT}, {USER_PROMPT}"

payload = {
    "prompt": full_prompt,
    "negative_prompt": "cartoon, 3d, painting, drawing, sketch, blurry, plastic, smooth, doll, low resolution, bad anatomy, text, watermark",
    "steps": 15,
    "width": 832,
    "height": 1216,
    "cfg_scale": 2.5,
    "sampler_name": "Euler a",
    "seed": -1
}

print(f"🚀 Generating Portrait: {USER_PROMPT[:50]}...")
try:
    response = requests.post(SD_API_URL, json=payload, timeout=300)
    if response.status_code == 200:
        r = response.json()
        if "images" in r:
            img_data = base64.b64decode(r["images"][0])
            filename = f"Flux_Portrait_{int(time.time())}.png"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            print(f"✅ Saved to: {filepath}")
except Exception as e:
    print(f"❌ Error: {e}")
