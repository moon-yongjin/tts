#!/usr/bin/env python3
"""
Draw Things Flux 배치 생성 (대본 기반 + Gemini 프롬프트 최적화)
"""
import os
import sys
import json
import requests
import base64
import time
import google.generativeai as genai

# ===== 설정 =====
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Batch_DrawThings")
SCRIPT_PATH = os.path.expanduser("~/projects/tts/대본.txt")
CONFIG_PATH = os.path.expanduser("~/projects/tts/config.json")

# 출력 폴더 생성
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== Gemini API 설정 =====
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)
    
genai.configure(api_key=config['Gemini_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# ===== 대본 읽기 =====
with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
    script_content = f.read()

print(f"📖 대본 로드 완료: {len(script_content)} 글자")

# ===== Gemini 프롬프트 생성 지침 (Flux 최적화) =====
PROMPT_INSTRUCTION = """
당신은 Flux 모델 전문 프롬프트 엔지니어입니다. 아래 한국어 대본을 읽고, **핵심 장면 1개**를 선택해 **영어 프롬프트**를 생성하세요.

**중요 규칙:**
1. **구체적 묘사**: 인물의 나이, 외모, 표정, 의상, 배경을 **극도로 구체적**으로 묘사하세요.
   - 나쁜 예: "an old woman"
   - 좋은 예: "A 72-year-old Korean woman, short gray hair, deep wrinkles, wearing a traditional hanbok, sitting in a modern apartment living room"

2. **카메라 앵글 명시**: 반드시 포함하세요.
   - 예: "Medium shot", "Close-up portrait", "Full body shot", "Over-the-shoulder view"

3. **조명 디테일**: 사실적인 조명 설정을 추가하세요.
   - 예: "Natural window light from the left", "Soft golden hour lighting", "Harsh overhead fluorescent light"

4. **감정 표현**: 인물의 감정을 **얼굴 근육 움직임**으로 묘사하세요.
   - 나쁜 예: "sad face"
   - 좋은 예: "Tears welling up in eyes, trembling lips, furrowed brow"

5. **Flux 스타일 키워드 필수 포함**:
   - "8k RAW photo, Fujifilm XT4, cinematic lighting, photorealistic, film grain, natural skin texture"

6. **금지 단어**: 절대 사용하지 마세요.
   - "beautiful", "perfect", "flawless", "stunning", "gorgeous" (너무 추상적)
   - "anime", "cartoon", "illustration" (스타일 혼동 유발)

**출력 형식 (JSON):**
```json
{{
  "prompt": "여기에 영어 프롬프트 (200단어 이내)",
  "scene_description": "선택한 장면 간단 설명 (한국어, 20자 이내)"
}}
```

**대본:**
{script}

지금 바로 JSON만 출력하세요. 다른 설명은 불필요합니다.
"""

# ===== 부정 프롬프트 (Flux 전용 강화) =====
NEGATIVE_PROMPT = """
cartoon, anime, 3d render, CGI, painting, drawing, sketch, illustration, 
plastic skin, doll-like, smooth skin, airbrushed, oversaturated colors,
blurry, out of focus, low resolution, pixelated, jpeg artifacts,
bad anatomy, deformed hands, extra fingers, missing limbs, floating limbs,
text, watermark, signature, logo, frame, border,
yellow skin, jaundice, unnatural skin tone, wax figure,
symmetrical face, perfect face, flawless skin, beauty filter
""".replace('\n', ' ').strip()

# ===== 이미지 생성 함수 =====
def generate_image(prompt_text, index):
    """Draw Things API로 이미지 생성"""
    print(f"\n🎨 [{index}/10] 생성 중...")
    print(f"   📝 프롬프트: {prompt_text[:80]}...")
    
    payload = {
        "prompt": prompt_text,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 20,              # Flux Dev는 20 스텝 권장
        "width": 832,
        "height": 1216,
        "cfg_scale": 3.5,         # Flux는 3.5가 최적
        "sampler_name": "Euler a",
        "seed": -1
    }
    
    try:
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                # 파일 저장
                timestamp = time.strftime("%H%M%S")
                filename = f"Flux_{index:02d}_{timestamp}.png"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                img_data = base64.b64decode(r["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                elapsed = time.time() - start_time
                print(f"   ✅ 완료: {filename} ({elapsed:.1f}초)")
                return True
            else:
                print("   ❌ 이미지 데이터 없음")
                return False
        else:
            print(f"   ❌ API 에러: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

# ===== 메인 실행 =====
def main():
    print("\n" + "="*60)
    print("  🚀 Flux Batch Generator (Draw Things + Gemini)")
    print("="*60)
    print(f"  📂 출력 폴더: {DOWNLOAD_DIR}")
    print(f"  🎯 목표: 10장 생성")
    print("="*60 + "\n")
    
    success_count = 0
    
    for i in range(1, 11):
        print(f"\n{'─'*60}")
        print(f"🔄 [{i}/10] Gemini 프롬프트 생성 중...")
        
        try:
            # Gemini로 프롬프트 생성
            prompt_request = PROMPT_INSTRUCTION.format(script=script_content)
            response = model.generate_content(prompt_request)
            
            # JSON 파싱 (마크다운 코드 블록 제거)
            response_text = response.text.strip()
            
            # DEBUG: 원본 응답 출력
            print(f"   🐛 DEBUG - 원본 응답:\n{response_text[:200]}...")
            
            # 코드 블록 제거 (여러 패턴 처리)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
            
            response_text = response_text.strip()
            
            # DEBUG: 파싱 전 텍스트
            print(f"   🐛 DEBUG - 파싱 전:\n{response_text[:200]}...")
            
            result = json.loads(response_text)
            prompt = result["prompt"]
            scene_desc = result.get("scene_description", "")
            
            print(f"   🎬 장면: {scene_desc}")
            print(f"   📝 프롬프트 길이: {len(prompt)} 글자")
            
            # 이미지 생성
            if generate_image(prompt, i):
                success_count += 1
            
            # API 레이트 리밋 방지
            if i < 10:
                time.sleep(2)
                
        except Exception as e:
            import traceback
            print(f"   ❌ Gemini 오류: {e}")
            print(f"   🐛 Full traceback:\n{traceback.format_exc()}")
            continue
    
    print("\n" + "="*60)
    print(f"  ✅ 완료: {success_count}/10 성공")
    print(f"  📂 결과 확인: {DOWNLOAD_DIR}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
