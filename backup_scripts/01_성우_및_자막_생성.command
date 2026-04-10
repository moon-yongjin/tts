#!/bin/bash
# [Azure 전용 커맨드 - 대량 처리용]
cd "$(dirname "$0")"

SCRIPT_PATH="01_성우_및_자막_생성.sh"

if [ ! -f "대본.txt" ]; then
    echo "❌ 대본.txt 파일을 찾을 수 없습니다."
    read -n 1 -s -r -p "계속하려면 아무 키나 누르세요..."
    exit 1
fi

echo "🚀 Azure 기반 성우 생성을 시작합니다 (1만자 지원)..."
START_TIME=$SECONDS
bash "$SCRIPT_PATH"

ELAPSED=$((SECONDS - START_TIME))
MIN=$((ELAPSED / 60))
SEC=$((ELAPSED % 60))
echo "------------------------------------------------"
echo "⏱️ [Azure 생성 완료] 총 소요 시간: ${MIN}분 ${SEC}초"
echo "------------------------------------------------"
read -n 1 -s -r -p "종료하려면 아무 키나 누르세요..."
