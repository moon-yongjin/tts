import requests
import base64
import os
import time

# Configuration
DRAW_THINGS_URL = "http://127.0.0.1:7860"
OUTPUT_DIR = "/Users/a12/Downloads/Chosun_Final"
FINAL_PROMPT = "(Masterpiece, best quality, 8k), a sturdy male traveler in dirty and worn-out off-white coarse hemp clothes (Joseon commoner's Bajijeogori), wearing a broad and sly smile (Smiling mischievously), pointing at the tavern's wine vat while talking, in the background, a stunningly beautiful young Korean woman with a K-pop idol-like face, featuring a charmingly wide mouth and big eyes, looks extremely flustered and embarrassed (Blushing and sweating), she is nervously fiddling with her fingers, looking down in shame after being caught diluting the wine, she has a surprisingly tall and large-framed, very voluptuous and curvy body (Plus size beauty), wearing a dirty off-white hemp top (Jeogori) and a matching dirty white hemp skirt (Chima) that clings to her figure, the fabric is stained with dust and grime (Gwangmok texture, aged), rustic Joseon-era tavern courtyard, cinematic lighting with warm sunset glow, photorealistic, highly detailed skin texture and embarrassed facial expression"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_final_scene():
    payload = {
        "prompt": FINAL_PROMPT,
        "negative_prompt": "low quality, distorted, static, text, watermark, changing background, morphing artifacts, bad anatomy, blur, double face, (worst quality, low quality:1.4), (bad anatomy), (inaccurate limb), (extra limbs), (disfigured:1.3), (deformed)",
        "steps": 8, # 국장님 요청: 8스텝
        "width": 1024,
        "height": 1536,
        "seed": -1,
        "guidance_scale": 1.0, # 터보 모델 최적화
        "sampler": "Euler A AYS", # 국장님 화면에서 확인된 최적 샘플러
        "shift": 3.2,
        "sharpness": 5
    }
    
    print(f"🚀 [Draw Things] 최종 반전 장면 생성 요청 중...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=300)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                filename = f"Chosun_Final_Scene_{int(time.time())}.png"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ [생성 완료] {filepath}")
                return filepath
        print(f"❌ 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    return None

if __name__ == "__main__":
    generate_final_scene()
