#!/bin/bash
# [Qwen-TTS 전용 서버 실행 커맨드]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/miniforge3/envs/qwen-tts/bin/python"
SERVER_SCRIPT="/Users/a12/projects/tts/qwen_instant_server.py"

echo "🚀 Qwen-TTS 초고속 서버를 시작합니다..."
echo "💡 이 창을 띄워두시면 성우 생성이 즉시(3초 내외) 이루어집니다."
echo "------------------------------------------------"

$PYTHON_EXE $SERVER_SCRIPT

echo "------------------------------------------------"
echo "⚠️ 서버가 종료되었습니다."
read -n 1 -s -r -p "종료하려면 아무 키나 누르세요..."
