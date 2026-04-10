#!/bin/bash

# 1. 경로 설정
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXE="/Users/a12/miniforge3/bin/python3"

echo "=================================================="
echo "🎙️  [STEP 01-3-7-1] 유튜브(52) & 유튜브(57) 멀티 보컬"
echo "📍 나레이션: 유튜브 (1-3-52)"
echo "📍 대사: 유튜브 (1-3-57)"
echo "📍 대상: $PROJECT_DIR/대본.txt"
echo "--------------------------------------------------"

cd "$PROJECT_DIR"

# 2. 파이썬 마스터 스크립트 실행
"$PYTHON_EXE" qwen3-tts-apple-silicon/zeroshot_scripts/01-3-7-1_Multi_Speaker_Master.py

echo "=================================================="
echo "✅ 마스터 트랙 생성이 완료되었습니다."
echo "📂 Downloads 폴더에서 결과를 확인하세요."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
