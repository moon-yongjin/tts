#!/bin/bash
# RUN_VISUAL_STUDIO.command
cd "$(dirname "$0")"

# Python 환경 설정
PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

if [ ! -f "$PYTHON_EXE" ]; then
    PYTHON_EXE="python3"
fi

echo "🎨 [Visual Studio] 웹 인터페이스를 실행합니다..."
echo "🌐 접속 주소: http://localhost:8501"
echo "--------------------------------------------------"

$PYTHON_EXE -m streamlit run WebUI/visual_studio.py --server.port 8501 --server.address 0.0.0.0
