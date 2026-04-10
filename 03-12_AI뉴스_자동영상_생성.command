#!/bin/bash
# 03-12_AI뉴스_자동영상_생성.command

# 터미널 창 유지 및 작업 디렉토리 설정
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/03-12_ai_news_cinematic.py"

echo "=================================================="
echo "🎥 [STEP 03-12] AI 뉴스 깔끔 무빙 영상 생성 시작"
echo "📍 설정: 빈티지 효과 제거 / 30fps / 고화질"
echo "--------------------------------------------------"

$PYTHON_EXE "$SCRIPT_PATH"

echo "=================================================="
echo "✅ 영상 생성이 완료되었습니다."
echo "📂 이미지 폴더 내의 .mp4 파일들을 확인하세요."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
 Elisa
