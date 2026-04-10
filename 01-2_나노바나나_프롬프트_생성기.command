#!/bin/bash
# 터미널 창 크기 조절
printf '\e[8;40;100t'

# 실행 위치를 스크립트 위치로 변경
cd "$(dirname "$0")"

PYTHON_PATH="/Users/a12/miniforge3/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/01-2_nanobanana_prompt_generator.py"

clear
echo "=========================================="
echo "    🍌 나노바나나 프롬프트 자동 생성기 🍌"
echo "=========================================="
echo "대본.txt 파일을 읽어 에셋과 장면 프롬프트를 생성합니다."
echo ""

echo "1. 캐릭터 에셋 개수를 입력하세요 (기본값: 4):"
read -p "> " CHAR_COUNT
if [ -z "$CHAR_COUNT" ]; then
    CHAR_COUNT=4
fi

echo ""
echo "2. 배경 에셋 개수를 입력하세요 (기본값: 4):"
read -p "> " BG_COUNT
if [ -z "$BG_COUNT" ]; then
    BG_COUNT=4
fi

echo ""
echo "3. 화풍(스타일)을 선택하세요 (기본값: 1):"
echo "  1) 극사실주의 (Photorealistic)"
echo "  2) 데이브 더 다이버 3D 게임 렌더 (Dave the Diver 3D Style)"
echo "  3) 시네마틱 수채화 (Cinematic Watercolor)"
echo "  4) 지브리 애니메이션 (Ghibli Anime)"
read -p "> " STYLE_OPT

STYLE_CHOICE="Photorealistic"
if [ "$STYLE_OPT" == "2" ]; then
    STYLE_CHOICE="DaveTheDiver"
elif [ "$STYLE_OPT" == "3" ]; then
    STYLE_CHOICE="Watercolor"
elif [ "$STYLE_OPT" == "4" ]; then
    STYLE_CHOICE="Ghibli"
fi

echo ""
echo "=========================================="
echo "설정 완료! 캐릭터: ${CHAR_COUNT}명 / 배경: ${BG_COUNT}곳 / 화풍: ${STYLE_CHOICE}"
echo "AI 프롬프트 생성을 시작합니다..."
echo "=========================================="
echo ""

"$PYTHON_PATH" "$SCRIPT_PATH" --chars "$CHAR_COUNT" --bgs "$BG_COUNT" --style "$STYLE_CHOICE"

echo ""
echo "=========================================="
echo "작업이 완료되었습니다."
echo "나노바나나_프롬프트.txt 파일을 확인해주세요."
echo "창을 닫으려면 엔터를 누르세요."
read
