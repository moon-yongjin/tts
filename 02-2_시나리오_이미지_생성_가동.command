#!/bin/bash

# [02-2 스태틱 이미지 전용 생성 가동]
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "--------------------------------------------------"
echo "🎨 [STEP 02-2] 수채화풍 시나리오 이미지 생성 시작"
echo "👉 프롬프트: 13개 장면 (Watercolor Style)"
echo "📡 ComfyUI 연결 중... (127.0.0.1:8188)"
echo "--------------------------------------------------"

cd "$PROJECT_DIR"

# 파이썬 실행
"$PYTHON_EXE" 02-2_Static_Image_Gen.py

echo ""
echo "--------------------------------------------------"
echo "✅ 모든 이미지 생성이 완료되었습니다."
echo "📂 다운로드 폴더에서 'Story_Scenes_...' 폴더를 확인하세요."
echo "--------------------------------------------------"
read -p "엔터를 누르면 종료됩니다."
