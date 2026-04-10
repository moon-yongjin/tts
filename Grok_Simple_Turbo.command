#!/bin/bash
# [Grok Simple Turbo] 국장님 전용 쾌속 생성기

echo "----------------------------------------------------"
echo "🏎️ Grok Simple Turbo v1.0"
echo "----------------------------------------------------"
echo "동작: 그록 열기 -> 파일 업로드 -> '.' 입력 -> 엔터"
echo "방식: 2개 파일씩 병렬 무한 반복"
echo "입력: ~/Downloads/Grok_Video_Input"
echo "----------------------------------------------------"

PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/grok_simple_turbo.py"

$PYTHON_PATH $SCRIPT_PATH
