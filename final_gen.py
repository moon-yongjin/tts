import requests
import base64
import os
import time

url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
save_dir = "/Users/a12/Downloads/Final_Scenes_Check"
os.makedirs(save_dir, exist_ok=True)

neg = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration, simple background, korean text, hangul, subtitles, lettering, writing, fonts, alphabets, words, characters, typography, headings, labels, signs"
q_suf = ", (masterpiece, high quality, 8k, photorealistic, historical Joseon Dynasty setting, cinematic lighting, ultra-detailed, depth of field), (NO TEXT, NO LETTERS:1.5)"

prompts = [
    "A cinematic medium shot of an elderly wealthy Korean nobleman with a long white beard wearing a luxurious pale blue silk durumagi handing over a large ring of traditional iron keys to his beautiful young daughter in her late teens wearing a white jeogori with a soft pink chima. Inside a traditional Korean house at night. Warm candle lighting.",
    "A cinematic wide shot of two young Korean women in their early 20s, one in a green jeogori and the other in a yellow jeogori, standing in a dark corner of a traditional room, looking deeply sad, jealous, and disappointed. In the blurred background, their father is handing keys to their younger sister."
]

names = ["Key_Handover", "Sisters_Sad"]

for i, p in enumerate(prompts):
    print(f"--- Attempting {names[i]} ---")
    payload = {
        "prompt": p + q_suf,
        "negative_prompt": neg,
        "sampler_name": "Euler A AYS",
        "steps": 8,
        "cfg_scale": 1.5,
        "width": 720,
        "height": 1280,
        "model": "z_image_turbo_1.0_q8p.ckpt"
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if "images" in data:
                img_data = base64.b64decode(data["images"][0])
                with open(f"{save_dir}/{names[i]}.png", "wb") as f:
                    f.write(img_data)
                print(f"SAVED: {save_dir}/{names[i]}.png")
            else:
                print("No images in response")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Ex: {e}")
