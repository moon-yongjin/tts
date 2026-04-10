#!/bin/bash
# [05-2 AI 효과음 전용 배치]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "--------------------------------------------------"
echo "🔊 [STEP 05-2] AI 효과음 전용 배치 가동 (BGM 제외)"
echo "--------------------------------------------------"

"$PYTHON_EXE" core_v2/05-2_ai_sfx_only_director.py
