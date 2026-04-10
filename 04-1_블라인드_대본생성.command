#!/bin/bash
# [04-1 블라인드 대본생성 시스템]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

clear
echo "=================================================="
echo "📝 [블라인드 쇼츠 대본 생성기 작동 준비]"
echo "=================================================="
echo "나무위키나 뉴스 기사의 팩트를 붙여넣기 기능으로 입력하시면,"
echo "AI가 이름을 끝까지 숨기다가 터뜨리는 쇼츠 문법으로 자동 변환합니다."

"$PYTHON_EXE" story_maker/blind_storyteller.py

echo ""
echo "엔터 키를 누르면 창이 닫힙니다."
read
