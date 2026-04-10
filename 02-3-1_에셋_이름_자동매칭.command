#!/bin/bash
# 02-3-1_에셋_이름_자동매칭.command

# [설정]
BASE_DIR="/Users/a12/projects/tts"
PYTHON_PATH="/Users/a12/miniforge3/bin/python"
RENAMER_PATH="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/asset_auto_renamer.py"
ASSETS_DIR="$HOME/Downloads/assets"

# 가장 최근 생성된 마스터 JSON 찾기
MASTER_JSON=$(ls -t "$BASE_DIR"/*_master.json 2>/dev/null | head -n 1)

clear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 AI 에셋 이름 자동 매칭 시스템 (Asset Auto-Renamer)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -z "$MASTER_JSON" ]; then
    echo "❌ 에러: 분석된 마스터 JSON 파일을 찾을 수 없습니다."
    echo "먼저 02-3번(프롬프트 생성)을 완료해 주세요."
    exit 1
fi

echo "📄 마스터 파일: $(basename "$MASTER_JSON")"
echo "📁 대상 폴더: $ASSETS_DIR"
echo ""
echo "🤖 AI가 파일명을 분석하여 CHAR_01, LOC_01 등으로 자동 변경합니다..."
echo ""

$PYTHON_PATH "$RENAMER_PATH" --master "$MASTER_JSON" --dir "$ASSETS_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 모든 작업이 완료되었습니다! 이제 Whisk 생성을 시작하셔도 됩니다."
else
    echo ""
    echo "❌ 작업 중 오류가 발생했습니다."
fi

echo ""
echo "위 창을 닫으려면 아무 키나 누르세요..."
read -n 1
