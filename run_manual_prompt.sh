#!/bin/bash

# 설정
PYTHON_PATH="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/02-99_manual_flux_gen.py"

# Python 스크립트가 없으면 생성
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "📜 Python 생성 스크립트 작성 중..."
    cat <<EOF > "$SCRIPT_PATH"
import os
import sys
import requests
import base64
import time

# 설정
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Flux_Manual_Test")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 스타일 (Flux Realism)
STYLE_PROMPT = "Photorealistic, 8k RAW photo, Fujifilm XT4, Cinematic Lighting, Skin texture detail, Weathered face, Hyper-realistic eyes, Subtle cinematic grain, <lora:flux-RealismLora:0.8>"

def generate(user_prompt):
    print(f"\n🚀 [Flux] 생성 시작: '{user_prompt}'")
    
    # 프롬프트 조립
    full_prompt = f"{STYLE_PROMPT}, {user_prompt}"
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": "cartoon, 3d, painting, drawing, sketch, blurry, plastic, smooth, doll, low resolution, bad anatomy, text, watermark",
        "steps": 4,
        "width": 1024,
        "height": 576,
        "cfg_scale": 1.0,
        "sampler_name": "Euler a",
        "seed": -1
    }
    
    try:
        start_time = time.time()
        response = requests.post(SD_API_URL, json=payload, timeout=300)
        
        if response.status_code == 200:
            end_time = time.time()
            r = response.json()
            if "images" in r and len(r["images"]) > 0:
                # 파일명 생성 (시간 + 프롬프트 앞부분)
                timestamp = time.strftime("%H%M%S")
                safe_prompt = "".join([c if c.isalnum() else "_" for c in user_prompt])[:20]
                filename = f"Flux_{timestamp}_{safe_prompt}.png"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                img_data = base64.b64decode(r["images"][0])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                print(f"✅ 생성 완료: {filepath}")
                print(f"⏱️ 소요 시간: {end_time - start_time:.2f}초")
            else:
                print("❌ 이미지 데이터 없음")
        else:
            print(f"❌ API 에러: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        generate(prompt)
    else:
        print("❌ 프롬프트를 입력해주세요.")
EOF
fi

# 사용자 입력 반복 루프
echo "=========================================="
echo "🎨 Flux Realism 수동 생성기 (M4 Pro)"
echo "=========================================="
echo "프롬프트를 입력하고 엔터를 누르세요."
echo "(종료하려면 'q' 또는 'exit' 입력)"
echo "------------------------------------------"

while true; do
    read -p "프롬프트 입력 > " USER_PROMPT
    
    if [[ "$USER_PROMPT" == "q" || "$USER_PROMPT" == "exit" ]]; then
        echo "👋 프로그램을 종료합니다."
        break
    fi
    
    if [[ -z "$USER_PROMPT" ]]; then
        echo "⚠️ 내용을 입력해주세요."
        continue
    fi
    
    "$PYTHON_PATH" "$SCRIPT_PATH" "$USER_PROMPT"
    echo "------------------------------------------"
done
