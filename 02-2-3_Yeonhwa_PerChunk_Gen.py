import requests
import json
import base64
import os
import time
import re
from datetime import datetime

# 1. 설정
DRAWTHINGS_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OUTPUT_BASE_DIR = os.path.expanduser("~/Downloads")
TIMESTAMP = datetime.now().strftime("%m%d_%H%M")
SAVE_DIR = os.path.join(OUTPUT_BASE_DIR, f"Yeonhwa_PerChunk_{TIMESTAMP}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 공통 설정
COMMON_NEGATIVE = "easynegative, human_low_quality, bad_anatomy, distorted_face, blurry, lowres, text, watermark, signature, modern_clothing, western_features, 3d, render, illustration"
COMMON_PARAMS = {
    "sampler_name": "Euler A AYS",
    "steps": 6,
    "cfg_scale": 1.0,
    "width": 720,
    "height": 1280,
    "negative_prompt": COMMON_NEGATIVE,
    "seed": 2024,
    "model": "z_image_turbo_1.0_q8p.ckpt",
    "shift": 3.0,
    "sharpness": 6
}

# 3. 캐릭터 및 배경 정의 (Consistency)
IDO_YOUNG = "A 20-year-old Korean nobleman (IDO), fine purple silk hanbok, traditional topknot (SANGTU), arrogant and cold facial features, sharp chin."
YEONHWA_YOUNG = "A beautiful 18-year-old Korean woman (YEONHWA), humble cotton hanbok, long dark hair tied lowly, sad and teary eyes."
IDO_OLD_BEGGAR = "A miserable 30-year-old Korean beggar man (IDO), extremely dirty and thin face, matted messy hair, wearing torn and filthy rags."
YEONHWA_SUCCESS = "An extraordinarily beautiful 28-year-old Korean merchant woman (YEONHWA), elegant and expensive red silk hanbok, sophisticated traditional hairstyle (JJOK-MEORI) with golden hairpin (BINYEO), dignified and cold aura."

BG_HANOK_GRAND = "Grand traditional Korean wooden house (Hanok), ornate wooden porch, sliding paper doors, stone base."
BG_STREET_MARKET = "Old dusty street of 18th century Seoul, traditional market stalls, blurry crowd, sunset lighting."
BG_PALANQUIN_DETAIL = "Luxurious traditional Korean palanquin (Gama), gold embroidery, silk curtains."

def split_chunks(text, max_chars=100):
    lines = text.splitlines()
    final_chunks = []
    for line in lines:
        line = line.strip()
        if not line: continue
        sentences = re.findall(r'[^,!?\s][^,!?\n]*[,!?\n]*', line)
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(current_chunk) + len(s) + 1 <= max_chars:
                current_chunk = (current_chunk + " " + s).strip()
            else:
                if current_chunk: final_chunks.append(current_chunk)
                current_chunk = s
        if current_chunk: final_chunks.append(current_chunk)
    return [c.strip() for c in final_chunks if c.strip()]

def get_scene_prompt(chunk_idx, chunk_text):
    """지문 순서에 따른 맞춤형 프롬프트 생성"""
    idx = chunk_idx + 1
    
    # 1~9: 과거 (결혼생활 및 추방)
    if 1 <= idx <= 3:
        return f"(Cinematic shot), {IDO_YOUNG} sitting on {BG_HANOK_GRAND}, looking down with contempt, {YEONHWA_YOUNG} kneeling on the floor, daytime."
    elif 4 <= idx <= 5:
        return f"(Wide shot), {YEONHWA_YOUNG} serving small snacks to {IDO_YOUNG} who is reclining arrogantly on a wooden porch."
    elif 6 <= idx <= 7:
        return f"(Action shot), {IDO_YOUNG} drunk, kicking {YEONHWA_YOUNG} in the chest, spilled dishes across the floor, dynamic and violent shadows, night."
    elif 8 <= idx <= 9:
        return f"(Melancholy shot), {YEONHWA_YOUNG} crying, leaving through the wooden gate of {BG_HANOK_GRAND} at night, carrying a small cloth bundle, rain."
    
    # 10~18: 10년 후 (거지 이도)
    elif 10 <= idx <= 12:
        return f"(Wide shot, historical drama style), 10 years later, {BG_STREET_MARKET} at dusk, {IDO_OLD_BEGGAR} wandering aimlessly."
    elif 13 <= idx <= 16:
        return f"(Close-up), {IDO_OLD_BEGGAR} with a desperate face, holding a dirty bowl, begging for money on the dusty street."
    elif 17 <= idx <= 18:
        return f"(Low angle), A magnificent {BG_PALANQUIN_DETAIL} passing through a crowded market, {IDO_OLD_BEGGAR} watching it with hungry eyes."
    
    # 19~21: 가마 앞에서의 조우
    elif 19 <= idx <= 21:
        return f"(Dramatic shot), {IDO_OLD_BEGGAR} prostrating on the ground in front of {BG_PALANQUIN_DETAIL}, guards looking down at him, dirty hands reaching out."
    
    # 22~27: 연화의 등장 및 심판
    elif 22 <= idx <= 23:
        return f"(Extremely close-up), {YEONHWA_SUCCESS} looking out from inside the palanquin, parting the silk curtains, cold and elegant face, golden accessories."
    elif 24 <= idx <= 25:
        return f"(Portrait), {YEONHWA_SUCCESS} looking down with a dignified smile, powerful female merchant leader aura, beautiful traditional makeup."
    elif 26 <= idx <= 27:
        return f"(Cinematic shot), A servant's hand throwing a piece of rotten meat to {IDO_OLD_BEGGAR} who is crying in the dirt, {BG_PALANQUIN_DETAIL} in the background."
    
    # 28~30: 마무리 (비참한 최후 및 교훈)
    elif 28 <= idx <= 30:
        return f"(Poetic wide shot), {IDO_OLD_BEGGAR} sitting alone in the cold shadows of an alley, {BG_PALANQUIN_DETAIL} disappearing into the distance, twilight, emotional atmosphere."
    
    return f"(Cinematic shot), {YEONHWA_SUCCESS} and {IDO_OLD_BEGGAR} in a historical Korean setting, dramatic lighting."

def generate_image(prompt, name, index):
    print(f"🎨 [{index}/{30}] 생성 중: {name}")
    payload = COMMON_PARAMS.copy()
    payload["prompt"] = prompt + ", (masterpiece, high quality, realistic skin texture, photorealistic, historical drama style)"
    payload["seed"] = 2024 + index
    
    try:
        response = requests.post(DRAWTHINGS_URL, json=payload, timeout=200)
        if response.status_code == 200:
            result = response.json()
            image_data = base64.b64decode(result['images'][0])
            file_path = os.path.join(SAVE_DIR, f"{name}.png")
            with open(file_path, "wb") as f:
                f.write(image_data)
            return True
    except Exception as e:
        print(f"  ❌ 에러: {e}")
    return False

def main():
    script_path = "/Users/a12/projects/tts/대본.txt"
    if not os.path.exists(script_path):
        print("❌ 대본 파일이 없습니다.")
        return
        
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    chunks = split_chunks(text)
    print(f"🚀 총 {len(chunks)}개의 청크 이미지 생성 시작 (저장: {SAVE_DIR})")
    
    for i, chunk in enumerate(chunks):
        prompt = get_scene_prompt(i, chunk)
        name = f"Yeonhwa_Chunk_{i+1:02d}"
        generate_image(prompt, name, i+1)
        # time.sleep(0.5)

    print(f"\n✅ 완료! {SAVE_DIR} 폴더를 확인하세요.")

if __name__ == "__main__":
    main()
