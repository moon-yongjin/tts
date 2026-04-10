import os
import json
import re
import time
import requests
import base64
from datetime import datetime
from google import genai
from google.genai import types

# 1. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")

# 2. 드로띵(DrawThings) API 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Characters_대본_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 3. 모델 설정 (02-2-3과 동일)
COMMON_NEGATIVE = (
    "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, "
    "(extravagant makeup:1.2), (k-pop idol style:1.4), (pretty:1.3), (handsome:1.3), flashy jewelry, "
    "(sexy:1.5), (revealing clothes:1.5), shorts, tank top, crop top, "
    "3d, render, illustration, (plastic surgery look:1.2), doll-like, anime, unrealistic skin, "
    "out of frame, poorly drawn hands, poorly drawn face"
)
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

def check_and_start_draw_things():
    check_app = os.popen('pgrep -x "Draw Things"').read().strip()
    if not check_app:
        print("🚀 드로띵 앱 실행 시도 중...")
        os.system('open -a "Draw Things"')
        time.sleep(15) # 부팅 시간 고려
    for i in range(5):
        try:
            requests.get("http://127.0.0.1:7860/sdapi/v1/options", timeout=3)
            return True
        except:
            time.sleep(5)
    return False

def extract_characters_with_gemini(script_text, api_key):
    client = genai.Client(api_key=api_key)

    system_prompt = """
    You are an AI that extracts characters from a script and creates high-quality cinematic prompts for Stable Diffusion.
    Focus on photorealism, realistic sizes, and dramatic, authentic descriptions. NO IDOL looks.
    
    ### [Mandatory Clothing Rule]
    - ALL characters MUST be described as wearing WARM WINTER CLOTHING (e.g., thick coat, padded jacket, wool sweater) suitable for Cold November weather in Korea, to prevent any skin exposure or revealing looks.
    - EXCEPT: description ONLY dictates otherwise if the script explicitly demands it (like Grandma's 'thin pajama').
    
    ### [Mandatory Background & Framing Rule]
    - Background MUST be a clean, neutral, solid gray or off-white studio background.
    - NEVER include ANY situational locations, weather, actions, scenes, or items from the script in the background.
    - Focus solely on the character's face, neck, and shoulders with NO background context.

    ### [Mandatory Unique Character Rule]
    - Create a HIGHLY DISTINCT and UNIQUE visual signature for each character (e.g., specific pattern scarf, particular wire glasses, a unique mole, highly specific hairstyle with gray streaks).
    - Ensure they look like distinct, castable real-life actors, NOT a generic default elderly/young face asset.
    
    OUTPUT MUST BE A VALID JSON with THE EXACT FORMAT:
    {
      "characters": [
        {
          "name": "인물이름",
          "description": "Cinamatic description for prompting (English only). cinematic portrait of an ordinary Korean [Age] [Gender], [Highly unique visual signature features], [warm winter clothing details like wool coat], against a solid neutral gray studio background. no makeup, raw skin."
        }
      ]
    }
    Extract the 2-4 primary main characters from the script dynamically.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[system_prompt, f"Script: {script_text}"],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        # 새 SDK는 response.text가 리스트 형태일 수 있으므로 안전하게 처리
        raw_text = response.text if isinstance(response.text, str) else response.text[0] if response.text else "{}"
        match = re.search(r'\{.*\}', raw_text.strip(), re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"❌ Gemini 추출 실패: {e}")
    return {"characters": []}

def generate_image(prompt, name):
    print(f"🎨 생성 시작: {name}")
    payload = COMMON_PARAMS.copy()
    quality_suffix = ", cinematic portrait, high quality, photorealistic, 8k, natural skin texture"
    payload["prompt"] = prompt + quality_suffix
    payload["seed"] = -1 # 랜덤
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                image_data = base64.b64decode(result['images'][0])
                file_path = os.path.join(SAVE_DIR, f"{name}.png")
                with open(file_path, "wb") as f:
                    f.write(image_data)
                print(f"📦 생성 완료: {name}.png")
                return True
        else:
            print(f"  ❌ 에러 코드: {response.status_code}")
    except Exception as e:
         print(f"  ❌ 생성 시 예외 발생: {e}")
    return False

def main():
    print("\n🎬 [Character Generator] 모델 가동")

    # 1. 설정 로드
    if not os.path.exists(CONFIG_PATH):
        print("❌ config.json 파일이 없습니다."); return
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        api_key = config.get("Gemini_API_KEY")

    if not api_key:
        print("❌ Gemini_API_KEY를 찾을 수 없습니다."); return

    # 2. 드로띵 연결 체크
    if not check_and_start_draw_things():
        print("❌ 드로띵 앱을 열거나 연결할 수 없습니다."); return
    print("✅ 드로띵 연결 성공!")

    # 3. 대본 로드
    script_path = os.path.join(BASE_DIR, "대본.txt")
    if not os.path.exists(script_path):
        print("❌ 대본.txt 파일이 없습니다."); return
    
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 4. 캐릭터 추출
    print("📝 Gemini를 이용해 캐릭터 정보 추출 중...")
    data = extract_characters_with_gemini(script_text, api_key)
    
    if not data or "characters" not in data:
        print("❌ 캐릭터 정보를 추출하지 못했습니다."); return

    characters = data["characters"]
    print(f"🔍 추출된 캐릭터 수: {len(characters)}명")

    # 🎥 데이터셋용 카메라 앵글/감정 베리에이션
    SUB_PROMPTS = [
        "cinematic close-up portrait, looking at camera",
        "medium shot cinematic portrait, body turned slightly",
        "dramatic side profile, cinematic lighting",
        "intense facial expression, emotional mood"
    ]

    for i, char in enumerate(characters):
        name = char.get("name")
        base_prompt = char.get("description")
        
        print(f"\n[{i+1}/{len(characters)}] 🎭 {name} 데이터셋 생성 중...")
        
        # 인물별 전용 하위 폴더 생성
        char_dir = os.path.join(SAVE_DIR, name)
        os.makedirs(char_dir, exist_ok=True)

        for j, sub_view in enumerate(SUB_PROMPTS):
            # 베이스 프롬프트에 동적 앵글 주입
            final_prompt = f"{sub_view}, {base_prompt}"
            file_name = f"{name}_{j+1:02d}"
            save_path = os.path.join(char_dir, file_name)
            
            print(f"   🎬 Variation {j+1}/4: {sub_view[:50]}...")
            
            # generate_image 함수가 파일명을 하위 폴더 경로를 포함하도록 오버라이딩
            generate_image_to_dir(final_prompt, save_path)

    print(f"\n✨ 모든 캐릭터 데이터셋 완성! {SAVE_DIR}")
    os.system(f"open '{SAVE_DIR}'")

def generate_image_to_dir(prompt, full_save_path):
    payload = COMMON_PARAMS.copy()
    quality_suffix = ", cinematic portrait, high quality, photorealistic, 8k, natural skin texture"
    payload["prompt"] = prompt + quality_suffix
    payload["seed"] = -1 # 랜덤
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                image_data = base64.b64decode(result['images'][0])
                # 변수가 경로를 직접 주입받음
                with open(full_save_path + ".png", "wb") as f:
                    f.write(image_data)
                print(f"      📦 저장 완료: {os.path.basename(full_save_path)}.png")
                return True
    except Exception as e: pass
    return False

if __name__ == "__main__":
    main()
