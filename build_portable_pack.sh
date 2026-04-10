#!/bin/bash

# Change internal folder name to ensure it looks new
PKG_NAME="Moohyup_Generator_Final"
PKG_DIR="/Users/a12/Downloads/$PKG_NAME"
PROJECT_DIR="/Users/a12/projects/tts"

echo "📦 [1/6] Preparing Workspace..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"
mkdir -p "$PKG_DIR/bin"

echo "📥 [2/6] Downloading Windows Python (Embedded)..."
# Download Python 3.10 Embed
curl -s -L -o python.zip https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip
unzip -q python.zip -d "$PKG_DIR/python"
rm python.zip

# Enable 'import site' in python310._pth to allow pip to work
# Mac sed requires empty string for extension
sed -i '' 's/^#import site/import site/' "$PKG_DIR/python/python310._pth"

echo "📥 [3/6] Downloading get-pip.py..."
curl -s -L -o "$PKG_DIR/python/get-pip.py" https://bootstrap.pypa.io/get-pip.py

echo "📥 [4/6] Downloading Windows FFmpeg..."
# Download FFmpeg (BtbN Build commonly used)
curl -s -L -o ffmpeg.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
unzip -q ffmpeg.zip -d ffmpeg_temp
# Find and move ffmpeg.exe/ffprobe.exe regardless of folder structure
find ffmpeg_temp -name "ffmpeg.exe" -exec mv {} "$PKG_DIR/bin/" \;
find ffmpeg_temp -name "ffprobe.exe" -exec mv {} "$PKG_DIR/bin/" \;
rm -rf ffmpeg_temp ffmpeg.zip

echo "📂 [5/6] Copying Project Files..."
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

# Create requirements.txt (Ensure it exists)
echo "google-genai==0.3.0" > "$PKG_DIR/requirements.txt"
echo "azure-cognitiveservices-speech==1.42.0" >> "$PKG_DIR/requirements.txt"
echo "pydub==0.25.1" >> "$PKG_DIR/requirements.txt"
echo "requests==2.32.3" >> "$PKG_DIR/requirements.txt"
echo "pillow==10.4.0" >> "$PKG_DIR/requirements.txt"
echo "numpy==1.26.4" >> "$PKG_DIR/requirements.txt"
echo "moviepy==1.0.3" >> "$PKG_DIR/requirements.txt"

# Copy Script/Key
cp "$PROJECT_DIR/대본.txt" "$PKG_DIR/"
if [ -f "$PROJECT_DIR/core_v2/service_account.json" ]; then
    cp "$PROJECT_DIR/core_v2/service_account.json" "$PKG_DIR/core_v2/"
fi

# Create Config JSON with PRE-FILLED KEYS (User Request)
echo '{
  "ElevenLabs_API_KEY": "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d",
  "Gemini_API_KEY": "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA",
  "Azure_Speech_Key": "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn",
  "Azure_Region": "koreacentral"
}' > "$PKG_DIR/config.json"


echo "📝 [6/6] Creating Bootstrap Batch File..."
# Create the MAIN batch file that installs pip/requirements on first run
cat > "$PKG_DIR/START_GENERATOR.bat" << 'EOF'
@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

:: [환경 설정]
set PYTHON_HOME=%~dp0python
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%~dp0bin;%PATH%

echo ====================================================
echo 🚀 [무협 비디오 원클릭 생성기]
echo ====================================================

:: [1. 파이썬 확인]
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 파이썬 실행 오류! python 폴더가 손상되었습니다.
    pause
    exit /b
)

:: [2. 라이브러리 설치 확인 (pip)]
if not exist "%PYTHON_HOME%\Scripts\pip.exe" (
    echo 📦 [최초 실행] 패키지 관리자(pip)를 설치합니다...
    python python\get-pip.py --no-warn-script-location
    
    echo 📦 [최초 실행] 필수 라이브러리를 설치합니다...
    python -m pip install -r requirements.txt --no-warn-script-location
    
    echo ✅ 설치 완료!
    echo.
)

:: [3. 메인 스크립트 실행]
echo ▶️ 생성기를 시작합니다...
call windows_scripts\99_전체_프로세스_통합_실행.bat

pause
EOF






# [Script File Setup]
# 1. Cleaner: Remove any old identical files
rm -f "$PKG_DIR/대본.txt"
rm -f "$PKG_DIR/대본_입력.txt"

# 2. Copy and Rename to ENGLISH (Safe)
# "SCRIPT_INPUT.txt" avoids any filename encoding issues on Windows
echo "🔄 Preparing script file..."
cp "$PROJECT_DIR/대본.txt" "$PKG_DIR/SCRIPT_INPUT.txt"

# 3. Convert Content to CP949 (EUC-KR) for Korean Windows Compatibility
# Filename is English (Safe), Content is CP949 (Windows Standard)
python3 -c "import codecs; text = open('$PROJECT_DIR/대본.txt', 'r', encoding='utf-8').read(); open('$PKG_DIR/SCRIPT_INPUT.txt', 'w', encoding='cp949', errors='replace').write(text)" 2>/dev/null || echo "❌ Encoding conversion failed"

echo "✨ Compressing..."
cd "/Users/a12/Downloads"
rm -f "Moohyup_Generator_Windows.zip"

# Zip recursively
zip -r "Moohyup_Generator_Windows.zip" "$PKG_NAME"

echo "✅ Done! /Users/a12/Downloads/Moohyup_Generator_Windows.zip"
