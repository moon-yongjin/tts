#!/bin/bash

# Grok extension automation bridge launcher
# This script starts the FastAPI bridge and opens Grok.

echo "----------------------------------------------------"
echo "🏎️ Grok Extension Turbo v2.0 (Bridge Mode) 가동"
echo "----------------------------------------------------"

# 1. Kill any existing server on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 2. Check dependencies
pip3 install fastapi uvicorn 1>/dev/null 2>&1

# 3. Start the Bridge Server in background
echo "🔗 [1/2] 브라우저 연결용 브릿지 서버를 시작합니다..."
python3 /Users/a12/projects/tts/core_v2/grok_bridge_server.py > /tmp/grok_bridge.log 2>&1 &

# 4. Open Grok Imagine
echo "🌐 [2/2] 그록(Grok) 페이지를 엽니다..."
open -a "Google Chrome" "https://grok.com/imagine"

echo "----------------------------------------------------"
echo "✅ 준비 완료! 이제 크롬에서 확장 프로그램을 켜시면 됩니다."
echo "이미지는 ~/Downloads/Grok_Video_Input 폴더에 넣으세요."
echo "----------------------------------------------------"
