#!/bin/bash

# 1. 경로 설정
# 현재 스크립트의 디렉토리로 이동 (루트 기준)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
MLX_DIR="$PROJECT_DIR/qwen3-tts-apple-silicon"

echo "=================================================="
echo "🎙️  [STEP 01-7-2] 클로이(Chloe) 전용 로컬 음성 생성 시작"
echo "📍 대상 대본: $PROJECT_DIR/대본.txt"
echo "📍 방식: LoRA 어댑터 (chloe_lora.safetensors)"
echo "--------------------------------------------------"

# 2. 실행 권한 확인 및 가상환경 진입
if [ ! -d "$MLX_DIR/.venv" ]; then
    echo "❌ 가상환경(.venv)이 존재하지 않습니다. 설치를 먼저 진행해 주세요."
    exit 1
fi

cd "$MLX_DIR"
source .venv/bin/activate

# 3. 파이썬 스크립트 실행
python3 01-7-2_chloe_lora_gen.py --script "$PROJECT_DIR/대본.txt"

echo "=================================================="
echo "✅ 생성이 완료되었습니다."
echo "📂 다운로드 폴더에서 '01-7-2클로이_로컬_*.wav' 및 '.srt' 파일을 확인하세요."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
