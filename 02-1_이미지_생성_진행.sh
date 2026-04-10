#!/bin/bash
# [02-1 이미지 생성 진행 - 세로 실사 모드]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "--------------------------------------------------"
echo "📸 [STEP 02-1] 프리미엄 세로 실사 이미지 생성을 시작합니다."
echo "--------------------------------------------------"
echo "👉 9:16 비율, 시네마틱 실사 스타일로 고정되어 있습니다."
# 매개변수로 수량을 받음 (기본값 없음)
IMG_COUNT=$1

if [ -z "$IMG_COUNT" ] || [ "$IMG_COUNT" == "AUTO" ]; then
    echo "💡 [자동 모드] 음성 길이에 맞춰 자동으로 수량을 계산합니다."
    "$PYTHON_EXE" core_v2/02-1_visual_director_916_realistic.py
else
    echo "💡 [고정 모드] 입력된 수량($IMG_COUNT)으로 생성을 진행합니다."
    "$PYTHON_EXE" core_v2/02-1_visual_director_916_realistic.py --count "$IMG_COUNT"
fi
