#!/bin/bash
# [SilentGrok] 백그라운드 원클릭 비디오 생성기

echo "----------------------------------------------------"
echo "🛰️ SilentGrok v1.0 - Stealth Mode"
echo "----------------------------------------------------"
echo "화면 없이 백그라운드에서 조용히 영상을 생성합니다."
echo "프롬프트 최적화: '.' (최단 시간 생성)"
echo "입력 대기: ~/Downloads/Grok_Video_Input"
echo "----------------------------------------------------"

PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/background_grok_video_gen.py"

# 백그라운드 프로세스로 실행
$PYTHON_PATH $SCRIPT_PATH
