#!/bin/bash
# [1-3-81 Qwen3-TTS 듀얼스피커 실행 커맨드]

# 스크립트 위치로 이동
cd "/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon"

# 전용 가상환경의 파이썬 실행
PYTHON_EXE="/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon/.venv/bin/python3"
SCRIPT_PATH="/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/1-3-81_ZeroShot_DualSpeaker_Classic_Angry.py"

clear
echo "--------------------------------------------------"
echo "🎙️ [STEP 1-3-81] 듀얼 스피커 (나레이션+대사) TTS 가동"
echo "   - 일반: 클래식언니 (배속)"
echo "   - 대사: 분노 목소리 (일반)"
echo "--------------------------------------------------"
echo ""

$PYTHON_EXE $SCRIPT_PATH

echo ""
echo "--------------------------------------------------"
echo "✅ 작업이 완료되었습니다."
echo "--------------------------------------------------"
read -p "엔터를 누르면 종료됩니다..."
