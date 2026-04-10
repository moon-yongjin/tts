#!/bin/bash
# [1-3-53 Qwen3-TTS ZeroShot 실행 커맨드 - 강아지]

# 스크립트 위치로 이동
cd "/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon"

# 전용 가상환경의 파이썬 실행
PYTHON_EXE="/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon/.venv/bin/python3"
SCRIPT_PATH="/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon/zeroshot_scripts/1-3-53_ZeroShot_Dog_TTS.py"

clear
echo "--------------------------------------------------"
echo "🎙️ [STEP 1-3-53] Qwen3-TTS ZeroShot TTS 가동 (강아지)"
echo "--------------------------------------------------"
echo ""

$PYTHON_EXE $SCRIPT_PATH

echo ""
echo "--------------------------------------------------"
echo "✅ 작업이 완료되었습니다."
echo "--------------------------------------------------"
read -p "엔터를 누르면 종료됩니다..."
