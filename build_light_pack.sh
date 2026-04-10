#!/bin/bash

# [Lightweight Version] Excludes Python & FFmpeg
PKG_NAME="Moohyup_Generator_Light"
PKG_DIR="/Users/a12/Downloads/$PKG_NAME"
PROJECT_DIR="/Users/a12/projects/tts"

echo "📦 [1/4] Preparing Workspace (Light)..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

# Skip Python/FFmpeg downloads

echo "📂 [2/4] Copying Project Files..."
# Copy Core
rsync -av "$PROJECT_DIR/core_v2" "$PKG_DIR/" \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude '.git' \
    --exclude 'models' \
    --exclude 'checkpoints' \
    --exclude '*.mp4'

# Copy Windows Scripts
mkdir -p "$PKG_DIR/windows_scripts"
cp "$PROJECT_DIR/windows_scripts/"*.bat "$PKG_DIR/windows_scripts/"

# Create requirements.txt
echo "google-genai==0.3.0" > "$PKG_DIR/requirements.txt"
echo "azure-cognitiveservices-speech==1.42.0" >> "$PKG_DIR/requirements.txt"
echo "pydub==0.25.1" >> "$PKG_DIR/requirements.txt"
echo "requests==2.32.3" >> "$PKG_DIR/requirements.txt"
echo "pillow==10.4.0" >> "$PKG_DIR/requirements.txt"
echo "numpy==1.26.4" >> "$PKG_DIR/requirements.txt"
echo "moviepy==1.0.3" >> "$PKG_DIR/requirements.txt"

# Copy Service Account if exists
if [ -f "$PROJECT_DIR/core_v2/service_account.json" ]; then
    cp "$PROJECT_DIR/core_v2/service_account.json" "$PKG_DIR/core_v2/"
fi


# Inject Keys (User Request)
echo '{
  "ElevenLabs_API_KEY": "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d",
  "Gemini_API_KEY": "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA",
  "Azure_Speech_Key": "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn",
  "Azure_Region": "koreacentral"
}' > "$PKG_DIR/config.json"

# [EXE Builder Setup]
cp "$PROJECT_DIR/launcher.py" "$PKG_DIR/"
cp "$PROJECT_DIR/BUILD_EXE.bat" "$PKG_DIR/"

# [Script File Setup]
# 1. Copy and Rename to ENGLISH (Safe)
cp "$PROJECT_DIR/대본.txt" "$PKG_DIR/SCRIPT_INPUT.txt"

# 2. Convert to CP949 (EUC-KR)
python3 -c "import codecs; text = open('$PROJECT_DIR/대본.txt', 'r', encoding='utf-8').read(); open('$PKG_DIR/SCRIPT_INPUT.txt', 'w', encoding='cp949', errors='replace').write(text)" 2>/dev/null

echo "📝 [3/4] Creating Bootstrap Batch File (System Python)..."
# Create a Light wrap that uses SYSTEM python
cat > "$PKG_DIR/START_GENERATOR_LIGHT.bat" << 'EOF'
@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

echo ====================================================
echo 🚀 [무협 비디오 생성기 - 라이트 버전]
echo ℹ️ Python 및 FFmpeg가 이미 설치되어 있어야 합니다.
echo ====================================================

:: [1. 파이썬 확인]
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 파이썬이 설치되어 있지 않거나 PATH에 없습니다.
    echo 👉 https://www.python.org/downloads/ 에서 파이썬을 설치해주세요.
    pause
    exit /b
)

:: [2. 라이브러리 자동 설치]
echo 📦 필수 라이브러리를 확인하고 설치합니다...
python -m pip install -r requirements.txt

:: [3. 메인 실행]
echo ▶️ 생성기를 시작합니다...
call windows_scripts\99_전체_프로세스_통합_실행.bat

pause
EOF

echo "✨ [4/4] Compressing..."
cd "/Users/a12/Downloads"
rm -f "Moohyup_Generator_Light.zip"

zip -r "Moohyup_Generator_Light.zip" "$PKG_NAME"

echo "✅ Done! /Users/a12/Downloads/Moohyup_Generator_Light.zip"
