#!/bin/bash
cd "/Users/a12/projects/tts"
clear
echo "=========================================="
echo "🎙️ [TikTok-Lite 04/03] Zero-Shot TTS 생성기"
echo "=========================================="
echo "💡 최신 동영상 레퍼런스를 사용하여 '대본.txt' 음성을 생성합니다."
echo ""

# Miniforge Python 환경 사용하여 실행
/Users/a12/miniforge3/bin/python "v1_7_74_ZeroShot_NewTikTok_0403.py"

echo ""
echo "✅ 작업이 완료되었습니다. Downloads 폴더를 확인하세요!"
echo ""
read -p "엔터를 누르면 종료됩니다..."
