import requests
import base64
import os
from datetime import datetime

DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"AutoDirector_Final_Scenes_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration, simple background, korean text, hangul, subtitles, lettering, writing, fonts, alphabets, words, characters, typography, headings, labels, signs"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

quality_suffix = ", (masterpiece, high quality, 8k, photorealistic, historical Joseon Dynasty setting, cinematic lighting, ultra-detailed, depth of field)"

prompts = [
    "A cinematic medium shot of an elderly, wealthy Korean nobleman (Jangja) with a long white beard, wearing a luxurious pale blue silk durumagi and a black gat, handing over a large ring of traditional iron warehouse keys to his beautiful young Korean daughter in her late teens, wearing a white jeogori with a soft pink chima. The scene takes place inside a traditional Korean 'Byeolchae' (detached house) at night. Hanji sliding doors, dark polished wooden floors, warm candle lighting. Jangja looks satisfied and wise, while Third Daughter looks humble yet receiving the keys with both hands. Cinematic lighting from a nearby candle. HDR, 8k, period drama style.",
    "A cinematic wide shot of an elderly, wealthy Korean nobleman (Jangja) with a long white beard, wearing a luxurious pale blue silk durumagi and a black gat, holding a wooden walking stick, handing a set of ornate keys to a beautiful young Korean woman in her late teens, wearing a white jeogori with a soft pink chima. She has a calm, wise, and serene expression. Inside a traditional Korean 'Byeolchae' (detached house) at night. Hanji sliding doors, dark polished wooden floors, warm candle lighting. In the corner, a young Korean woman in her early 20s, wearing a simple yet clean cream-colored hanbok with a green jeogori, and a young Korean woman in her early 20s, wearing a bright yellow jeogori and a navy blue chima, are standing, looking deeply sad and disappointed. Their faces show regret and jealousy. Darker lighting in their corner. HDR, 8k, period drama style."
]

names = ["20_Father_Giving_Keys", "21_Sisters_Sad"]

for i, prompt in enumerate(prompts):
    print(f"🎨 Generating {names[i]}...")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = prompt + quality_suffix
    payload["seed"] = -1
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                image_data = base64.b64decode(result['images'][0])
                file_path = os.path.join(SAVE_DIR, f"{names[i]}.png")
                with open(file_path, "wb") as f:
                    f.write(image_data)
                print(f"  ✅ Saved to {file_path}")
            else:
                print(f"  ❌ No images in response")
        else:
            print(f"  ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print(f"\n✨ Done! Folder: {SAVE_DIR}")
os.system(f"open {SAVE_DIR}")
