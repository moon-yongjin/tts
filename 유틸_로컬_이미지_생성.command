#!/bin/bash
# 유틸_로컬_이미지_생성.command

# 터미널 창 유지 및 작업 디렉토리 설정
cd "$(dirname "$0")"

# Python 경로 설정 (ComfyUI venv 사용)
PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/02-100_local_comfy_gen.py"

clear
echo "=================================================="
echo "🖼️  로컬 ComfyUI 이미지 생성 유틸리티"
echo "=================================================="
echo ""
echo "👉 생성하고 싶은 이미지의 프롬프트를 입력하세요 (영어 권장):"
read PROMPT

if [ -z "$PROMPT" ]; then
    echo "❌ 프롬프트가 입력되지 않았습니다. 종료합니다."
    sleep 2
    exit 1
fi

echo ""
echo "🎨 작업 시작..."
$PYTHON_EXE "$SCRIPT_PATH" "$PROMPT"

echo ""
echo "=================================================="
echo "✅ 작업이 완료되었습니다."
echo "💡 결과물은 ComfyUI Output 폴더를 확인하세요."
echo "=================================================="
echo ""
echo "엔터를 누르면 종료됩니다."
read
