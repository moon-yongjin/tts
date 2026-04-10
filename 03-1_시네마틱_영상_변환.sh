#!/bin/bash
# [03-1 빈티지 시네마 변환]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "🎬 [STEP 03-1] 빈티지 시네마 변환을 시작합니다..."
"$PYTHON_EXE" core_v2/03-1_cinematic_v3_vintage.py
