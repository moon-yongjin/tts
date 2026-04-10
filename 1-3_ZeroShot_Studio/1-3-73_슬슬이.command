#!/bin/bash
# [1-3-73 ScreenRecording ZeroShot 실행 커맨드]

# 스크립트 위치로 이동
cd "/Users/a12/projects/tts"

# 파이썬 실행
# (1-3-92 등에 명시된 miniforge3 파이썬 사용)
PYTHON_EXE="/Users/a12/miniforge3/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/1-3-73_ZeroShot_ScreenRecording_Direct_v5.py"

clear
echo "--------------------------------------------------"
echo "🎙️ [STEP 1-3-73] Qwen3-TTS ZeroShot ScreenRecording (틱톡직출)"
echo "--------------------------------------------------"
echo ""
echo "👉 레퍼런스 오디오: 다운로드 내 최신 TikTok.mp4"
echo "👉 대상 대본: 대본.txt"
echo ""

$PYTHON_EXE $SCRIPT_PATH

echo ""
echo "--------------------------------------------------"
echo "✅ 제로샷 음성 생성이 완료되었습니다."
echo "--------------------------------------------------"
read -p "엔터를 누르면 화면이 종료됩니다..."
