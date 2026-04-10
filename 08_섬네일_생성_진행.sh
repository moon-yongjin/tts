#!/bin/bash
# [08 섬네일 생성기 - ASS 기반]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "🎨 [STEP 08] ASS 기반 시네마틱 섬네일 제작을 시작합니다..."
"$PYTHON_EXE" core_v2/08_thumbnail_maker.py

echo ""
echo "작업이 완료되었습니다. Downloads 폴더를 확인하세요."
sleep 2
