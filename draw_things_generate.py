import requests
import json
import os
import time

DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = "/Users/a12/Downloads/Script_Scenes_Dynamic"

def generate_image(prompt, filename, steps=5, seed=-1):
    payload = {
        "prompt": prompt,
        "negative_prompt": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, blurry, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy",
        "steps": steps,
        "width": 640,
        "height": 640,
        "seed": seed,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler a",
        "shift": 3.0,  # Improved contrast
        "sharpness": 5, # lowered for more natural film look
        "seed_mode": "Scale Alike"
    }
    
    print(f"🚀 Generating: {filename}...")
    start_time = time.time()
    response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload)
    
    if response.status_code == 200:
        elapsed = time.time() - start_time
        print(f"✅ Success! ({elapsed:.1f}s)")
        data = response.json()
        # Draw Things returns base64 encoded images in 'images' key
        if "images" in data:
            import base64
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            for idx, img_b64 in enumerate(data["images"]):
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print(f"💾 Saved: {filepath}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    test_prompts = [
        "Early 1980s film photo, a sophisticated Korean woman in her 50s (Kyoung-sook), elegant emerald green silk dress, sharp almond eyes, looking at a luxurious tailor shop mirror, realistic skin texture, 35mm film grain, cinematic lighting, detailed fingers and face.",
        "Early 1980s film photo, an 75-year-old Korean woman (Bok-soon) with deeply wrinkled face and sharp eyes, faded blue floral headscarf, standing in a dark alley of Myeong-dong, holding a bunch of seaweed with realistic knuckles and fingers, vintage analog palette.",
        "Early 1980s film photo, dramatic interaction between Kyoung-sook and Bok-soon in the tailor shop, tension in their facial expressions, 1978 Seoul atmosphere, realistic textures, high detail."
    ]
    
    for i, p in enumerate(test_prompts):
        generate_image(p, f"DT_Test_{i+1}.png")
