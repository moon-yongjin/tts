#!/bin/bash
# [02 이미지 생성 진행 - MAC 전용]
cd "$(dirname "$0")"

# Python 환경 및 설정
PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "--------------------------------------------------"
echo "🎨 [STEP 02] 이미지 생성 설정을 시작합니다."
echo "--------------------------------------------------"
echo "👉 생성할 이미지 수량을 입력하세요 (기본값: 10, 자동 계산: 0)"
printf "입력 (Enter 시 10): "
read IMG_COUNT

# 입력값이 비어있으면 기본값 10 적용
if [ -z "$IMG_COUNT" ]; then
    IMG_COUNT=10
fi

echo ""
echo "🚀 총 $IMG_COUNT장의 이미지 생성을 시작합니다..."
echo "--------------------------------------------------"

"$PYTHON_EXE" core_v2/02_visual_director_96.py --count $IMG_COUNT
