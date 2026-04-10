#!/bin/bash

# 1. 경로 설정
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXE="/Users/a12/miniforge3/bin/python3"

echo "=================================================="
echo "🎙️  [STEP 01-3-50] Qwen3 새로운 목소리 클로닝 시작"
echo "📍 대상 대본: $PROJECT_DIR/대본.txt"
echo "📍 참고 음성: v3_new_6s_vocal (6s fixed)"
echo "📍 방식: MLX-Audio Zero-Shot (High Performance)"
echo "--------------------------------------------------"

cd "$PROJECT_DIR"

# 2. 파이썬 스크립트 실행
"$PYTHON_EXE" qwen3-tts-apple-silicon/1-3-50_ZeroShot_NewVoice_TTS.py

echo "=================================================="
echo "✅ 작업이 완료되었습니다."
echo "📂 Downloads 폴더에서 결과를 확인하세요."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
