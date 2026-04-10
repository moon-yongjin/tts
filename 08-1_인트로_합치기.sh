#!/bin/bash
# [08 인트로 영상 합치기]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "🎬 [STEP 08] 인트로 영상 합치기를 시작합니다..."
"$PYTHON_EXE" core_v2/08_video_intro_merger.py

