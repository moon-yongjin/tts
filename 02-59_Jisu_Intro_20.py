import requests
import json
import time
import os
import base64

# --- [설정 영역] ---
# 지수: 슬프지만 우아하고 아름다운 젊은 여성(20대 중반)
# 김 회장: 70대 초반, 탐욕스럽고 권위적인 눈빛의 재벌가 노인
CFG_SCALE = 1.0 
STEPS = 4
SEED = -1
OUTPUT_DIR = "/Users/a12/Downloads/Jisu_Intro_20"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMMON_PROMPT = "8k resolution, cinematic lighting, masterwork, 1980s retro cinematic film style, highly detailed textures, realistic skin, deep focus, sharp details,"

# 1-2행(장례식 & 감금/학대) 집중 20장 프롬프트
prompts = [
    # [1행: 장례식장] (1~10번) - 슬픔과 소유욕의 교차
    f"{COMMON_PROMPT} A grand luxury funeral hall in a mansion. Jisu (beautiful woman in white funeral hanbok) crying silently, looking at the altar.",
    f"{COMMON_PROMPT} Extreme close-up of Kim Chairman's (greedy 70s old man) slimy, lustful eyes staring at Jisu's white neck from a low angle.",
    f"{COMMON_PROMPT} Kim Chairman sitting in the mourner seat, clutching a cane, eyes glowing with unhealthy greed as he looks at Jisu.",
    f"{COMMON_PROMPT} The altar with a portrait of a young man, surrounded by white chrysanthemums, cold funeral atmosphere.",
    f"{COMMON_PROMPT} Kim Chairman approaching crying Jisu, whispering in her ear, his face is menacingly close and greedy.",
    f"{COMMON_PROMPT} Jisu looking up at Kim Chairman with horror and fear in her eyes at the funeral.",
    f"{COMMON_PROMPT} Kim Chairman's hand holding a bunch of debt papers, thrusting them towards Jisu's face.",
    f"{COMMON_PROMPT} Wide shot of the funeral hall, power dynamics clearly visible: Chairman standing high, Jisu kneeling alone.",
    f"{COMMON_PROMPT} Close up on Jisu's trembling hands clutching her white dress as the Chairman speaks.",
    f"{COMMON_PROMPT} Kim Chairman's sinister smirk reflecting in the funeral hall's polished floor.",
    
    # [2행: 오피스텔 감금/학대] (11~20번) - 화려한 감옥과 고통
    f"{COMMON_PROMPT} Jisu sitting alone in a cold, ultra-luxurious modern penthouse, looking out the dark city window.",
    f"{COMMON_PROMPT} Luxury jewelry (diamonds, pearls) scattered on a marble floor, looking like shackles.",
    f"{COMMON_PROMPT} Close up on a small hidden camera blinking red light in a bedroom closet, monitoring Jisu.",
    f"{COMMON_PROMPT} Kim Chairman entering Jisu's penthouse room at night, holding a glass of whiskey, eyes full of madness.",
    f"{COMMON_PROMPT} Kim Chairman shouting at Jisu, throwing a debt collector's notice on the bed.",
    f"{COMMON_PROMPT} Jisu covering her ears as Kim Chairman pours out verbal abuse, looking devastated.",
    f"{COMMON_PROMPT} A silhouette of Kim Chairman towering over Jisu who is cowering in a dark corner of the luxury room.",
    f"{COMMON_PROMPT} Close up on Jisu's face, her soul being shattered, eyes losing their spark.",
    f"{COMMON_PROMPT} The contrast of a beautiful golden birdcage in the room vs Jisu's trapped face.",
    f"{COMMON_PROMPT} Jisu looking at a small hidden recording device installed by her, a gaze of hidden hope for revenge."
]

def generate_images():
    print(f"🚀 [Jisu Intro] Starting 20-frame intensive render...")
    for i, prompt in enumerate(prompts):
        filename = f"Jisu_Intro_{i+1:02d}.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        payload = {
            "prompt": f"{prompt}, natural makeup, bare face look, soft cinematic, ultra-detailed textures, realistic lighting, 8k professional photography, film grain, photorealistic lighting setups, detailed surrounding atmosphere, 1980s retro aesthetics, raw texture",
            "negative_prompt": "heavy makeup, dark eyeliner, dark lips, text, watermark, banner, low quality, blurry, distorted, anime, cartoon, illustration, drawing, extra fingers, messy hands, distorted face, nsfw, naked, bad proportions, bad anatomy, doll face, plastic surgery, glamorous fit body, voluptuous, airbrushed, 3d, cg, cropped frame",
            "steps": 5,          # <- 스텝 수 5로 변경
            "width": 576,        # <- 폭 576로 변경
            "height": 1024,      # <- 높이 1024로 변경
            "seed": -1,
            "model": "z_image_turbo_1.0_q8p.ckpt",
            "guidance_scale": 1.0,
            "sampler": "Euler A AYS", # 최신 02-30~40 규격: Euler A AYS
            "shift": 3.0,
            "sharpness": 6,
            "seed_mode": "Scale Alike"
        }
        
        print(f"🎬 [{i+1}/20] Rendering: {filename}")
        try:
            response = requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json=payload)
            if response.status_code == 200:
                data = response.json()
                if "images" in data and len(data["images"]) > 0:
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(data["images"][0]))
                    print(f"✅ Saved: {filename}")
                time.sleep(1)
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    generate_images()
    print("🔥 Jisu Intro 20 frames generation complete!")
