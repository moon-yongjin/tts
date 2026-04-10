#!/bin/bash

# 1. 경로 설정
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXE="/Users/a12/miniforge3/bin/python3"

echo "=================================================="
echo "🎙️  [STEP 01-3-8] 멀티 화자 (01-3-5 & 01-3-57)"
echo "📍 나레이션: 01-3-5 (Art)"
echo "📍 대사: 01-3-57"
echo "📍 대상: $PROJECT_DIR/대본.txt"
echo "--------------------------------------------------"

cd "$PROJECT_DIR"

# 2. 파이썬 마스터 스크립트 실행
"$PYTHON_EXE" qwen3-tts-apple-silicon/zeroshot_scripts/01-3-8_Multi_Speaker_Master.py

echo "=================================================="
echo "✅ 마스터 트랙 생성이 완료되었습니다."
echo "📂 Downloads 폴더에서 결과를 확인하세요."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
