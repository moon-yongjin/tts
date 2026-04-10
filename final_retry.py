import requests
import base64
import os

url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
save_dir = "/Users/a12/Downloads/Final_Scenes_Check_2"
os.makedirs(save_dir, exist_ok=True)

neg = "easynegative, text, watermark, signature, modern, western, 3d, render, illustration, korean text, hangul, letters, alphabets, words, characters, typography, labels, signs"
q_suf = ", (masterpiece, high quality, 8k, photorealistic, historical Joseon Dynasty setting, cinematic lighting, ultra-detailed), (NO TEXT, NO LETTERS:1.8)"

prompts = [
    "A cinematic medium shot of an elderly Korean nobleman with a long white beard wearing a luxurious pale blue durumagi handing a large ring of iron keys to a beautiful young daughter in a pink chima. Inside a traditional house, warm candle lighting.",
    "A cinematic wide shot of two older Korean sisters in green and yellow jeogori standing in a dark corner of a traditional room, looking deeply sad and jealous, watching their younger sister receive keys from their father."
]

names = ["Scene_Final_Key", "Scene_Final_Sisters"]

for i, p in enumerate(prompts):
    print(f"Generating {names[i]}...")
    payload = {
        "prompt": p + q_suf,
        "negative_prompt": neg,
        "sampler_name": "Euler A AYS",
        "steps": 6,
        "cfg_scale": 1.0,
        "width": 720,
        "height": 1280,
        "model": "z_image_turbo_1.0_q8p.ckpt"
    }
    try:
        r = requests.post(url, json=payload, timeout=120)
        print(f"Response: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if "images" in data:
                img_data = base64.b64decode(data["images"][0])
                with open(f"{save_dir}/{names[i]}.png", "wb") as f:
                    f.write(img_data)
                print(f"Saved {names[i]}.png")
            else:
                print("No images found in response data")
        else:
            print(f"API Error: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")
