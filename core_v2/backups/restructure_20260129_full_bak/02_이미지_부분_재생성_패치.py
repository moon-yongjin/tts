from google import genai
from google.genai import types
from google.oauth2 import service_account
import os
import json
import time
import sys
import re

# [윈도우 호환성]
sys.stdout.reconfigure(encoding='utf-8')

# 1. 설정 및 서비스 계정 인증
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_PATH, "service_account.json")

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH,
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)
client = genai.Client(
    vertexai=True, 
    project="ttss-483505", 
    location="us-central1", 
    credentials=credentials
)

def get_latest_folder():
    base_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = [os.path.join(base_downloads, d) for d in os.listdir(base_downloads) 
               if os.path.isdir(os.path.join(base_downloads, d)) and d.startswith("무협_생성_")]
    if subdirs:
        return sorted(subdirs)[-1]
    return None

def run_patch():
    print("🛠️ [이미지 부분 재생성] 잘못된 스타일의 이미지만 골라 다시 뽑습니다.")
    
    # 1. 대상 폴더 확인
    target_dir = get_latest_folder()
    if not target_dir:
        print("❌ 대상 폴더를 찾을 수 없습니다.")
        return
    
    print(f"📂 대상 폴더: {target_dir}")
    
    # 2. 재생성할 번호 입력 받기
    user_input = input("👉 다시 생성할 이미지 번호를 쉼표로 구분해 입력하세요 (예: 5, 23, 41): ").strip()
    if not user_input:
        print("💡 입력이 없습니다. 종료합니다.")
        return
    
    try:
        indices = [int(x.strip()) for x in user_input.replace(",", " ").split() if x.strip().isdigit()]
    except Exception as e:
        print(f"❌ 입력 형식이 잘못되었습니다: {e}")
        return
    
    if not indices:
        print("❌ 유효한 번호가 없습니다.")
        return

    # 3. 대본 및 설정 로드
    script_path = os.path.join(BASE_PATH, "대본.txt")
    if not os.path.exists(script_path):
        print("❌ 대본.txt 파일을 찾을 수 없습니다.")
        return
    
    with open(script_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()
    
    # 설정 파일 찾기
    settings_files = [f for f in os.listdir(BASE_PATH) if f.startswith("visual_settings_") and f.endswith(".json")]
    if not settings_files:
        print("❌ 설정 파일을 찾을 수 없습니다.")
        return
    # 가장 최근 설정 파일 사용
    settings_path = os.path.join(BASE_PATH, sorted(settings_files, key=lambda x: os.path.getmtime(os.path.join(BASE_PATH, x)))[-1])
    
    with open(settings_path, "r", encoding="utf-8") as f:
        bible = json.load(f)

    # 4. 대본 분할 (기존 방식과 동일하게 96분할)
    total_chars = len(full_text)
    target_image_count = 96
    chars_per_image = max(5, round(total_chars / target_image_count))
    
    # 대본 뭉치 만들기
    text_clean = ' '.join(full_text.split())
    chunks = []
    start = 0
    while start < len(text_clean) and len(chunks) < 96:
        end = start + chars_per_image
        chunk = text_clean[start:end]
        chunks.append(chunk)
        start = end
    
    print(f"🚀 {len(indices)}개의 이미지를 '익스트림 스케치 프리셋'으로 재생성합니다.")

    # 5. 지정된 번호만 재생성
    for idx in indices:
        if idx < 1 or idx > len(chunks):
            print(f"⚠️ {idx}번: 범위를 벗어난 번호입니다. 스킵.")
            continue
            
        chunk = chunks[idx-1]
        print(f"\n--- [{idx:03d}번 재생성 시작] ---")
        
        # 스타일 강화 필터 (실사 방지용)
        sketch_style_boost = "Masterpiece hand-drawn charcoal sketch on rough paper. Dramatic rough pencil strokes. NO photocopism, NO realism, NO digital smooth textures. HIGH CONTRAST Black and White ART only."
        
        # 프롬프트 추출
        prompt_req = f"""
        [Task] Create a visual prompt for a CHARCOAL SKETCH based on the script below.
        [Script] {chunk}
        [Main Character] {bible.get('character_en', '')}
        [Background Context] {bible.get('background_en', '')}
        [Rule] Describe the scene for a rough pencil sketch. NO realism.
        [Output Format] Single English sentence.
        """
        
        try:
            response = client.models.generate_content(
                model="publishers/google/models/gemini-2.0-flash-001",
                contents=prompt_req
            )
            v_prompt = response.text.strip()
            
            # 이미지 생성 (Imagen)
            print(f"🎨 Imagen 생성 중 (096_스케치.png 형식)...")
            final_prompt = f"Style: {sketch_style_boost}. Scene: {v_prompt}"
            
            imagen_resp = client.models.generate_images(
                model='publishers/google/models/imagen-4.0-generate-001',
                prompt=final_prompt,
                config={'number_of_images': 1, 'aspect_ratio': '16:9'}
            )
            
            filename = f"{idx:03d}_스케치.png" # 현재는 '스케치' 고정
            filepath = os.path.join(target_dir, filename)
            
            img_obj = imagen_resp.generated_images[0]
            if hasattr(img_obj, 'image'):
                img_obj.image.save(filepath)
            else:
                with open(filepath, "wb") as f:
                    f.write(img_obj.image_bytes)
            
            print(f"✅ 완료: {filename}")
            
        except Exception as e:
            print(f"❌ {idx}번 생성 실패: {e}")

    print("\n✨ 선택한 이미지들의 재생성이 완료되었습니다!")

if __name__ == "__main__":
    run_patch()
