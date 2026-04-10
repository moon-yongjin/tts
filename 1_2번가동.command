#!/bin/bash
cd "/Users/a12/projects/tts"
read -p "🎥 시네마틱 영상 길이를 입력하세요 (초) [엔터=3.0초]: " duration
duration=${duration:-3.5}
export CINEMATIC_DURATION=$duration
/Users/a12/miniforge3/bin/python /Users/a12/projects/tts/1-4_Visual_Pipeline.py
echo ""
read -p "엔터를 누르면 종료됩니다..."
