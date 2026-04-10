#!/bin/bash
# [03-2-1 시네마틱 영상 변환 - 정사각형 에디션]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "--------------------------------------------------"
echo "🎥 [STEP 03-2-1] 프리미엄 정사각형 시네마틱 변환 가동"
echo "--------------------------------------------------"
echo "👉 1080x1080 1:1 해상도에 최적화된 연출을 적용합니다."

"$PYTHON_EXE" core_v2/03-2-1_cinematic_square.py
