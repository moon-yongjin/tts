#!/bin/zsh
echo "🚀 CapCut 자동 배치 스크립트를 실행합니다..."
cd "$(dirname "$0")"
python3 capcut_zoom_in.py
echo "✅ 작업이 완료되었습니다. 아무 키나 누르면 종료됩니다."
read -n 1
