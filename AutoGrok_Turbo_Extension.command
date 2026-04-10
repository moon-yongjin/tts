#!/bin/bash
# [AutoGrok Turbo Extension] 하이테크 푸시 엔진

echo "----------------------------------------------------"
echo "🚀 AutoGrok Turbo (Extension Push Mode)"
echo "----------------------------------------------------"
echo "폴더에 이미지를 넣으면 크롬 확장프로그램으로 즉시 '푸시'합니다."
echo "입력 대기: ~/Downloads/Grok_Video_Input"
echo "----------------------------------------------------"

# 서버 실행
PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
SERVER_PATH="/Users/a12/projects/tts/core_v2/grok_turbo_server.py"

echo "🛰️ 푸시 서버를 가동합니다..."
$PYTHON_PATH $SERVER_PATH
