import json
import requests
import time
import os
import base64
import concurrent.futures
import sys
from google import genai
from google.genai import types

# Configuration
DRAW_THINGS_URL = "http://127.0.0.1:7860"
DOWNLOADS_DIR = "/Users/a12/Downloads/Script_Scenes_Dynamic"
SCRIPT_FILE = "/Users/a12/projects/tts/대본.txt"
CONFIG_PATH = "/Users/a12/projects/tts/config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

# Gemini API 설정
GOOGLE_API_KEY = load_gemini_key()
if not GOOGLE_API_KEY:
    print("❌ API Key를 찾을 수 없습니다.")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def get_dynamic_prompts(script_text, count):
    """Gemini를 사용하여 대본에서 이미지 프롬프트를 추출합니다."""
    print(f"🤖 Gemini를 통해 {count}개의 이미지 프롬프트를 추출 중...")
    
    prompt = f"""
    당신은 헐리우드 촬영 감독입니다. 아래 대본을 읽고, 영상 제작을 위한 총 {count}개의 이미지 생성을 위한 고퀄리티 시각적 프롬프트를 작성해줘.
    
    [대본]
    {script_text}
    
    [요구사항]
    1. 각 프롬프트는 반드시 'Early 1980s film photo'로 시작할 것.
    2. 프롬프트 구성 (총 {count}개):
       - [Kyoung-sook]과 [Bok-soon]의 대립과 긴장감을 묘사할 것.
    3. 캐릭터 [시각적 고정 요소] 필축:
       - [Kyoung-sook]: "A sophisticated Korean woman in her 50s, sharp almond-shaped eyes, elegant perm hair, wearing an expensive emerald green silk dress with gold embroidery, pearl necklace."
       - [Bok-soon]: "A 75-year-old Korean woman with deeply wrinkled face, sharp piercing eyes, wearing a faded blue floral headscarf and a worn-out gray traditional quilted vest."
    4. 모든 장면에는 '35mm film grain'과 'Vintage analog color palette'를 포함할 것.
    5. 인물 및 장소 묘사 시 1978년 서울의 분위기를 극대화할 것.
    6. 아래 지침을 스타일에 활용: "shot on 35mm lens, f/1.8, shallow depth of field, blurred background, extreme bokeh, soft background, realistic skin texture, volumetric lighting, dramatic shadows, Kodak Portra 400 aesthetic, HD quality, strictly Korean ethnicity"
    7. 인물은 극도로 선명하게(extremely sharp subject), 배경은 매우 부드럽고 몽환적으로 아웃포커싱(very soft, dreamy blurred background) 되도록 묘사할 것.
    8. 반드시 아래 JSON 형식으로 항목을 응답할 것.
    
    [응답 형식]
    [
      "첫 번째 장면의 영어 프롬프트",
      "두 번째 장면의 영어 프롬프트",
      ...
    ]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        if response.parsed is not None:
            return response.parsed[:count]
        return json.loads(response.text)[:count]
    except Exception as e:
        print(f"⚠️ Gemini 추출 실패 ({e})")
        return []

def generate_scene_with_lora(scene_num, p_text, lora_file, lora_weight=0.8):
    prefix = lora_file.split('.')[0]
    filename = f"lora_{prefix}_Scene_{scene_num:02d}.png"
    
    payload = {
        "prompt": p_text,
        "negative_prompt": "foreigners, anime, cartoon, illustration, drawing, text, watermark, low quality, distorted, deformed, extra fingers, malformed hands, fused fingers, bad anatomy",
        "steps": 6,
        "width": 640,
        "height": 640,
        "seed": 2026 + scene_num,
        "model": "z_image_turbo_1.0_q8p.ckpt",
        "guidance_scale": 1.0,
        "sampler": "Euler a",
        "shift": 1.2,
        "sharpness": 2,
        "seed_mode": "Scale Alike",
        "loras": [
            {"file": lora_file, "weight": lora_weight}
        ]
    }
    
    print(f"[Queueing] {filename} (LoRA: {lora_file})...")
    try:
        response = requests.post(f"{DRAW_THINGS_URL}/sdapi/v1/txt2img", json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data["images"][0]))
                print(f"✅ [Complete] {filename}!")
                return filename
        print(f"❌ {filename} 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ {filename} 오류: {e}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_generate_loras.py <lora_file> [count]")
        sys.exit(1)
        
    lora_file = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    if os.path.exists(SCRIPT_FILE):
        with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
            script_text = f.read()
    else:
        script_text = "No script found."

    prompts = get_dynamic_prompts(script_text, count)
    if not prompts:
        print("❌ 프롬프트 추출 실패")
        sys.exit(1)

    print(f"\n🚀 LoRA [{lora_file}]를 적용하여 {len(prompts)}장의 이미지 생성을 시작합니다...")
    
    for i, p in enumerate(prompts):
        generate_scene_with_lora(i+1, p, lora_file)

    print(f"\n✨ 완료: {DOWNLOADS_DIR}")
