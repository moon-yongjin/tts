#!/bin/bash
# [Asset Auto-Mapper] 파일 이름 일괄 변경 커맨드

cd "$(dirname "$0")"

echo "=========================================="
echo "🖼️ 에셋 이름 자동 매칭 시작!"
echo "=========================================="

./venv_dt/bin/python Asset_Renamer.py

echo ""
read -p "엔터를 누르면 종료됩니다..."
