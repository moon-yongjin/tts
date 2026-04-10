#!/bin/bash
cd "$(dirname "$0")"
echo "🎙️ Supertone AI [Angry Male] Voice (01-3-56) 가동!"
echo "📍 대상 대본: /Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/대본.txt"
echo "------------------------------------------------"

# 가상환경 경로 및 스크립트 실행
/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/qwen3-tts-apple-silicon/.venv/bin/python3 01-3-56_supertone_angry_male_gen.py

echo "------------------------------------------------"
echo "✅ 작업이 완료되었습니다. 아무 키나 누르면 종료됩니다."
read -n 1
