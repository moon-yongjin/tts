#!/bin/bash

# 터미널 창 크기 조절
printf '\e[8;40;100t'

# 설정
PYTHON_PATH="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/02-99_manual_flux_gen.py"

# Python 스크립트 작성 (항상 덮어쓰기)
mkdir -p "$(dirname "$SCRIPT_PATH")"
cat <<EOF > "$SCRIPT_PATH"
import os
import sys
import requests
import base64
import time
import cv2
import json
import numpy as np
import re
from PIL import Image
import io

# [설정]
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
IMG2IMG_API_URL = "http://127.0.0.1:7860/sdapi/v1/img2img"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:latest"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Manual_Test")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# [스타일] Flux Realism
STYLE_PROMPT = "Photorealistic, 8k RAW photo, Fujifilm XT4, Cinematic Lighting, Skin texture detail, Weathered face, Hyper-realistic eyes, Subtle cinematic grain, film grain, high ISO, natural imperfections, skin pores, raw photo, <lora:flux-RealismLora:0.8>"

# [부정 프롬프트] 와이드 샷 강제 - 상반신/클로즈업 강력 금지
NEGATIVE_PROMPT = """
cartoon, anime, 3d render, CGI, painting, drawing, sketch, illustration, 
close-up, extreme close-up, headshot, face focus, zoomed in, macro,
upper body, waist up, bust up, medium shot, portrait, 
plastic skin, doll-like, smooth skin, airbrushed, oversaturated colors,
blurry, out of focus, low resolution, pixelated, jpeg artifacts,
bad anatomy, deformed hands, extra fingers, missing fingers, fused fingers, mutated hands, 
poorly drawn hands, malformed hands, long fingers, twisted fingers, broken fingers,
bad eyes, crossed eyes, lazy eye, asymmetric eyes, different sized eyes, misaligned eyes,
weird eyes, unnatural eyes, glowing eyes, red eyes, empty eyes, soulless eyes,
floating limbs, missing limbs, extra limbs, disconnected limbs,
text, watermark, signature, logo, frame, border,
yellow skin, jaundice, unnatural skin tone, wax figure,
symmetrical face, perfect face, flawless skin, beauty filter
""".replace('\n', ' ').strip()

def refine_prompt_with_ollama(user_input):
    print(f"🧠 [Ollama] Wide-Angle 구도로 프롬프트 재구성 중...")
    
    # 시스템 프롬프트에 Wide/Full-body 강제 지침 추가
    system_prompt = f"""
    Translate and refine this user input into a HIGH-QUALITY WIDE ANGLE English image prompt for Flux.1.
    
    [CRITICAL RULES]
    1. COMPOSITION: Always describe a "Wide cinematic shot", "Full body shot", or "Environmental portrait".
    2. PERSPECTIVE: Show the character's entire figure and the surrounding environment. 
    3. FORBIDDEN: Do NOT use "Upper body", "Waist up", or "Close up" unless explicitly requested by the user.
    4. Focus on hyper-realism, natural lighting, and detailed backgrounds.
    5. Output ONLY the final English prompt. NO <think> tags, NO labels.
    
    User Input: "{user_input}"
    Wide Cinematic English Prompt:
    """
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.6,
            "num_predict": 256
        }
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            raw_response = data.get("response", "").strip()
            
            # 검열 메시지 감지 로직 추가
            censorship_keywords = ["sorry", "cannot", "against my policy", "inappropriate", "ethical", "guideline", "죄송합니다", "수 없습니다", "정책에 따라"]
            if any(kw in raw_response.lower() for kw in censorship_keywords):
                print(f"⚠️ [Ollama] AI가 검열로 인해 답변을 거절했습니다. 원본 프롬프트로 생성을 시도합니다.")
                return user_input

            refined = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
            refined = refined.replace('"', '').replace("'", "").replace('`', '').strip()
            # 프롬프트 앞에 Wide Shot 명시 보강
            if "wide" not in refined.lower() and "full body" not in refined.lower():
                refined = "Wide cinematic shot, full body visible, " + refined
            return refined
    except Exception as e:
        print(f"⚠️ Ollama 처리 실패: {e}")
    return user_input

def detect_faces(image_array):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces

def inpaint_face(image_array, face_coords, original_prompt):
    x, y, w, h = face_coords
    margin = int(w * 0.3) # 넓은 샷에서는 마진을 조금 더 넓게
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(image_array.shape[1], x + w + margin)
    y2 = min(image_array.shape[0], y + h + margin)
    
    face_crop = image_array[y1:y2, x1:x2]
    # 너무 작은 얼굴은 보정 시 뭉글어질 수 있으므로 최소 크기 체크
    if face_crop.shape[0] < 20 or face_crop.shape[1] < 20:
        return image_array

    face_pil = Image.fromarray(face_crop)
    buffered = io.BytesIO()
    face_pil.save(buffered, format="PNG")
    face_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    payload = {
        "init_images": [face_b64],
        "prompt": f"{original_prompt}, intricate facial details, realistic eyes, natural skin texture, masterpiece",
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 15,
        "denoising_strength": 0.45, # 넓은 샷에서 작은 얼굴은 약간 더 높게
        "width": 512,
        "height": 512,
        "cfg_scale": 4.0,
        "sampler_name": "Euler a"
    }
    
    try:
        response = requests.post(IMG2IMG_API_URL, json=payload, timeout=120)
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                refined_face_data = base64.b64decode(r["images"][0])
                refined_face = Image.open(io.BytesIO(refined_face_data))
                refined_face_resized = refined_face.resize((x2-x1, y2-y1), Image.LANCZOS)
                result_array = image_array.copy()
                result_array[y1:y2, x1:x2] = np.array(refined_face_resized)
                return result_array
    except: pass
    return image_array

def generate(user_input):
    refined_prompt = refine_prompt_with_ollama(user_input)
    print(f"✨ [AI Prompt]: {refined_prompt}")
    
    full_prompt = f"{STYLE_PROMPT}, {refined_prompt}"
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 20,
        "width": 768,
        "height": 1024,
        "cfg_scale": 3.5,
        "sampler_name": "Euler a",
        "seed": -1
    }

    try:
        print(f"🚀 [Flux] 이미지 생성 중 (Wide-Angle)...")
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                img_data = base64.b64decode(r["images"][0])
                img = Image.open(io.BytesIO(img_data))
                img_array = np.array(img)
                
                faces = detect_faces(img_array)
                if len(faces) > 0:
                    print(f"   👤 얼굴 {len(faces)}개 감지됨, 보정 중...")
                    for face in faces:
                        img_array = inpaint_face(img_array, face, refined_prompt)
                
                final_img = Image.fromarray(img_array)
                timestamp = time.strftime("%H%M%S")
                safe_prompt = "".join([c if c.isalnum() else "_" for c in user_input])[:20]
                filename = f"Flux_Wide_{timestamp}_{safe_prompt}.png"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                final_img.save(filepath)
                print(f"✅ 생성 완료: {filename}")
                print(f"⏱️ 소요 시간: {time.time() - start_time:.2f}초")
            else:
                print("❌ 이미지 데이터 없음")
        else:
            print(f"❌ API 에러: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate(sys.argv[1])
EOF

# 메인 루프
clear
echo "=========================================="
echo "   🎨 Flux Wide-Angle Generator (Local)   "
echo "=========================================="
echo " * 엔진: Draw Things + Ollama (DeepSeek-R1)"
echo " * 특징: 전신 및 와이드 시네마틱 구도 고정"
echo " * 금지: 상반신 위주, 배경 없는 클로즈업"
echo " * 보정: 얼굴 인페인팅 자동 포함"
echo "=========================================="
echo ""

while true; do
    echo -n "📝 장면 입력 (한글/영어 / 종료: q) > "
    read USER_PROMPT
    
    if [[ "$USER_PROMPT" == "q" || "$USER_PROMPT" == "exit" ]]; then
        echo "👋 종료합니다."
        break
    fi
    
    if [[ -z "$USER_PROMPT" ]]; then
        continue
    fi
    
    "$PYTHON_PATH" "$SCRIPT_PATH" "$USER_PROMPT"
    echo ""
    echo "------------------------------------------"
done
