#!/bin/bash
# [Grok Turbo Calibrate] 좌표 설정용 커맨드

# 1. 파일이 위치한 디렉토리로 이동
cd "$(dirname "$0")"

echo "=========================================="
echo "🎯 Grok Turbo 좌표 캘리브레이션"
echo "=========================================="
echo "5초 뒤에 현재 마우스 좌표를 출력합니다."
echo "그록의 각 버튼 위에 마우스를 미리 올려두세요."
echo ""

# 2. 파이썬 가상환경 가동 및 캘리브레이션 모드 실행
./venv_dt/bin/python grok_py_bot.py cal

echo ""
read -p "엔터를 누르면 종료됩니다..."
