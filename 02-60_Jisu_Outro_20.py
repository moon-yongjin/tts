import requests
import json
import time
import os
import base64

# --- [설정 영역] ---
DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = "/Users/a12/Downloads/Jisu_Outro_20"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMMON_STYLE = "natural makeup, bare face look, soft cinematic, ultra-detailed textures, realistic lighting, 8k professional photography, film grain, 1980s retro aesthetics, raw texture"
NEGATIVE = "heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, doll face, plastic surgery, airbrushed, 3d, cg, cropped frame"

# 후반부(수행비서 등장 ~ 엔딩) 20개 시퀀스 프롬프트
prompts = [
    # [수행비서 등장 및 비밀 폭로]
    f"A loyal secretary (middle-aged man, stoic) secretly recording Kim Chairman's verbal abuse in a dark office, {COMMON_STYLE}",
    f"The secretary secretly handing a small USB recording device to Jisu in a dark marble corridor, suspenseful lighting, {COMMON_STYLE}",
    f"Jisu (beautiful woman) listening to the recording on a laptop in her dark room, eyes widening in shock and rage, {COMMON_STYLE}",
    f"Close up on Jisu's face, her sorrow turning into fierce determination for revenge, cold eye glint, {COMMON_STYLE}",
    f"Jisu looking at herself in a luxury mirror, wearing a hidden recorder under her dress for the party, {COMMON_STYLE}",
    
    # [파티장 폭로 클라이맥스]
    f"A wide shot of a grand luxury anniversary party, sparkling chandeliers, many socialites in suits, {COMMON_STYLE}",
    f"Jisu standing on a grand party stage, holding a microphone, looking calm but determined, {COMMON_STYLE}",
    f"A giant screen at the party suddenly showing Kim Chairman’s distorted greedy face and audio waves, {COMMON_STYLE}",
    f"The party guests looking shocked and whispering as the chairman's abusive voice plays through speakers, {COMMON_STYLE}",
    f"Kim Chairman on the VIP seat, his face turning pale and hands trembling with rage, {COMMON_STYLE}",
    f"Jisu shouting 'I am not this beast's toy!' into the microphone, full of tragic dignity, {COMMON_STYLE}",
    f"Press reporters flashing cameras at the exposed Kim Chairman, absolute chaos at the party, {COMMON_STYLE}",
    
    # [체포 및 몰락]
    f"Police officers in 1980s uniforms entering the grand party hall, surrounding Kim Chairman, {COMMON_STYLE}",
    f"Close up on shiny silver handcuffs being snapped onto Kim Chairman's wrinkled wrists, {COMMON_STYLE}",
    f"Kim Chairman being dragged away by police, his expensive tuxedo wrinkled, looking defeated, {COMMON_STYLE}",
    f"Jisu watching the chairman being dragged away from a distance, a cold and relief expression, {COMMON_STYLE}",
    f"The grand logo of the corporation flickering or falling, symbolizing the fall of the empire, {COMMON_STYLE}",
    
    # [2부 떡밥 및 엔딩]
    f"A heavy secret safe door slowly opening in Chairman's dark hidden room, revealing mysterious papers, {COMMON_STYLE}",
    f"Jisu looking at her antique necklace, finding a hidden engraving or compartment, mystery vibes, {COMMON_STYLE}",
    f"Ending shot: Jisu walking towards the bright sunlight away from the luxury mansion, 'To be continued' vibes, {COMMON_STYLE}"
]

def generate_outro():
    print(f"🚀 [Jisu Outro] Starting 20-frame intensive render with 720x1280...")
    for i, p in enumerate(prompts):
        filename = f"Jisu_Outro_{i+1:02d}.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        payload = {
            "prompt": p,
            "negative_prompt": NEGATIVE,
            "steps": 5,
            "width": 576,    # 형님 지시 규격 (576)
            "height": 1024,  # 형님 지시 규격 (1024)
            "seed": -1,
            "model": "z_image_turbo_1.0_q8p.ckpt",
            "guidance_scale": 1.0,
            "sampler": "Euler A AYS",
            "shift": 3.0,
            "sharpness": 6
        }
        
        print(f"🎬 [{i+1}/20] Rendering: {filename}")
        try:
            response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
            if response.status_code == 200:
                data = response.json()
                if "images" in data:
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(data["images"][0]))
                    print(f"  ✅ Saved: {filename}")
                time.sleep(1)
            else:
                print(f"  ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    generate_outro()
    print("🔥 Jisu Outro 20 frames complete!")
