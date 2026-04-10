import os
import json
import time
import sys
import re
import requests
import base64
from datetime import datetime
import google.generativeai as genai

# 1. 설정 및 인증
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"

genai.configure(api_key=API_KEY)

# DrawThings API 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"AutoDirector_NewStory_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 3. 이미지 생성 공통 파라미터 (철저한 리얼리즘 및 평범함 추구)
COMMON_NEGATIVE = (
    "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, "
    "(extravagant makeup:1.2), (k-pop idol style:1.4), (pretty:1.3), (handsome:1.3), (beautiful:1.3), flashy jewelry, "
    "western_features, 3d, render, illustration, simple background, korean text, hangul, subtitles, lettering, "
    "writing, fonts, alphabets, words, characters, typography, headings, labels, signs, (plastic surgery look:1.2), "
    "doll-like, anime, unrealistic skin, (split screen:1.5), multi-panel, collage, grid, duplicate, (two images:1.5), "
    "out of frame, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of focus, long neck"
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
        print("🚀 드로띵 앱 실행 중...")
        os.system('open -a "Draw Things"')
        time.sleep(10)
    for i in range(5):
        try:
            requests.get("http://127.0.0.1:7860/sdapi/v1/options", timeout=2)
            return True
        except:
            time.sleep(5)
    return False

def get_visual_bible():
    """평범한 일상 인물을 강조한 비주얼 가이드"""
    return {
        "CHARACTERS": {
            "MIL_YEONGRAN": "The Protagonist, an ordinary Korean woman in her early 60s. Short greyish permed hair, natural aging wrinkles around eyes and mouth, absolutely no makeup. Wearing a simple cotton shirt or house blouse. She looks like someone's real grandmother or mother from the neighborhood.",
            "DIL": "The Antagonist, a Korean woman in her 30s. Average-looking, practical hair, wearing common office-look or home-look clothes. Slightly tired or annoyed expression, not a model type. A realistic everyday woman.",
            "SADON": "DIL's mother, a wealthy Korean woman in her 60s. Looks slightly more polished but still realistic. Wearing a colorful luxury scarf and pearl necklace, looking proud or surprised.",
        },
        "SETTING_GUIDELINES": {
            "KOREAN_HOME": "Realistic middle-class Korean apartment with everyday items (drying rack, plastic containers, semi-cluttered kitchen). Real domestic lighting.",
            "SADON_HOUSE": "A slightly cleaner, more luxurious living room with a leather sofa and large TV, but still within the Korean apartment aesthetic.",
        }
    }

def get_dynamic_prompt(chunk_text, visual_bible):
    """대본 문체분석을 통한 인물 및 현대 극 실사 프롬프트 생성 (클린업 강화)"""
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    system_prompt = f"""
    You are an AI that converts Korean scripts into STABLE DIFFUSION PROMPTS. 
    OUTPUT ONLY THE RAW PROMPT STRING. NO EXPLANATIONS. NO 'Here's the prompt'. NO MARKDOWN.
    
    [VISUAL BIBLE]
    {json.dumps(visual_bible, indent=2)}

    [MISSION]
    1. Convert the script into a single, high-quality visual description for Stable Diffusion.
    2. Focus on the main character in the scene.
    3. Use simple, direct, photorealistic English.
    4. NO TEXT, NO split screen, NO multi-panel.
    
    FORMAT: A cinematic [Shot Type] of the character [Action] in [Setting]. [Details].
    """

    try:
        response = model.generate_content([system_prompt, f"Script: {chunk_text}"])
        prompt = response.text.strip()
        
        # [핵심] 불필요한 AI 대화문 제거 로직
        lines = prompt.split('\n')
        prompt_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            # AI의 의례적인 말투나 마크다운 태그, 분석글 제외
            if any(x in line.lower() for x in ["okay,", "here is", "here's", "analysis:", "context:", "prompt:", "visual:", "breakdown:", "script:"]):
                continue
            if line.startswith("**") or line.startswith("* "):
                continue
            prompt_lines.append(line)
        
        # 유효한 프롬프트 행만 합치기
        clean_prompt = " ".join(prompt_lines)
        if not clean_prompt or len(clean_prompt) < 15: 
            # 만약 필터링 결과가 너무 짧으면 원본에서 최대한 추출
            clean_prompt = prompt.replace("```", "").replace("prompt:", "").split('\n')[-1].strip()

        # 최종 클리닝 (서두의 라벨 제거)
        clean_prompt = re.sub(r'^(Prompt|PROMPT|Visual Description|Image Prompt):?\s*', '', clean_prompt, flags=re.IGNORECASE)
        
        return clean_prompt, "Scene: " + chunk_text[:20]
    except Exception as e:
        print(f"❌ Gemini 프롬프트 생성 실패: {e}")
        return "A cinematic shot of an ordinary elderly Korean woman, 8k, realistic drama style.", "Scene: Default"

def generate_dt_image(prompt, name, index):
    print(f"🎨 [{index}] 생성 중: {name}")
    payload = COMMON_PARAMS.copy()
    quality_suffix = ", (masterpiece, high quality, 8k, photorealistic, realistic Korean household, non-idol faces, natural skin texture)"
    payload["prompt"] = prompt + quality_suffix
    payload["seed"] = -1
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                image_data = base64.b64decode(result['images'][0])
                file_path = os.path.join(SAVE_DIR, f"{name}.png")
                with open(file_path, "wb") as f:
                    f.write(image_data)
                return True
    except Exception as e:
        print(f"  ❌ 생성 시 예외 발생: {e}")
    return False

def main():
    if not check_and_start_draw_things():
        return

    script_path = "/Users/a12/projects/tts/대본.txt"
    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read()
    
    bible = get_visual_bible()
    raw_chunks = re.split(r'\n\s*\n', full_text.strip())
    chunks = [c.strip() for c in raw_chunks if c.strip()]
    total = len(chunks)
    
    print(f"\n🚀 총 {total}개 장면 생성 시작 (저장: {SAVE_DIR})")
    
    for i, chunk in enumerate(chunks):
        scene_num = i + 1
        prompt, _ = get_dynamic_prompt(chunk, bible)
        print(f"\n📝 [Scene {scene_num}/{total}] Prompt 추출됨")
        print(f"   > {prompt[:100]}...")
        
        name = f"{scene_num:02d}_Auto_Director"
        generate_dt_image(prompt, name, scene_num)
        
    print(f"\n✨ 작업 완료! {SAVE_DIR}")
    os.system(f"open {SAVE_DIR}")

if __name__ == "__main__":
    main()
