#!/bin/bash

# [설정]
BASE_DIR="/Users/a12/projects/tts"
PYTHON_SCRIPT="$BASE_DIR/core_v2/02-0_visual_master_generator.py"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧠 비주얼 마스터 JSON 자동 생성 시스템 (Master Generator)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📄 대상 대본: $BASE_DIR/대본.txt"
echo "🤖 AI가 대본을 분석하여 에셋(캐릭터, 장소) 정의를 자동 생성합니다..."
echo ""

# Python 스크립트 실행
python3 "$PYTHON_SCRIPT"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 모든 작업이 완료되었습니다! 'visual_prompts_master.json'이 갱신되었습니다."
    echo ""
else
    echo ""
    echo "❌ 오류가 발생했습니다. 로그를 확인해 주세요."
    echo ""
fi

echo "위 창을 닫으려면 아무 키나 누르세요..."
read -n 1 -s
