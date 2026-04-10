#!/bin/bash
# [03-2 시네마틱 영상 변환 - 세로 에디션]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/miniforge3/bin/python3"

echo "--------------------------------------------------"
echo "🎥 [STEP 03-2] 프리미엄 세로 시네마틱 변환 가동"
echo "--------------------------------------------------"
echo "👉 1080x1920 세로 해상도에 최적화된 연출을 적용합니다."

"$PYTHON_EXE" core_v2/03-2_cinematic_v3_vertical.py
