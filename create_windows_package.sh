#!/bin/bash

# Configuration
PROJECT_DIR="/Users/a12/projects/tts"
PKG_DIR="${PROJECT_DIR}/TTS_Windows_Pack_Signed"
ZIP_NAME="${PROJECT_DIR}/TTS_Windows_Pack_Signed.zip"
DOWNLOADS_DIR="/Users/a12/Downloads"

echo "📦 Packaging for Windows..."

# 1. Clean previous build
rm -rf "$PKG_DIR"
rm -f "$ZIP_NAME"
mkdir -p "$PKG_DIR"

# 2. Copy Core Logic (core_v2)
# Exclude venv, __pycache__, heavy models, git, etc.
# Note: User wants "Library" (resources) included.
rsync -av --progress "$PROJECT_DIR/core_v2" "$PKG_DIR/" \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'venv' \
    --exclude '.git' \
    --exclude 'models' \
    --exclude 'checkpoints' \
    --exclude '*.mp4' \
    --exclude '*.mp3' \
    --exclude 'ffmpeg' 

# Re-include Library audio files if they were excluded by *.mp3 rule above?
# rsync excludes are pattern based. 'Library' folder itself is copied.
# But inside Library/bgm/*.mp3 might be excluded.
# Let's verify and force include Library contents.
rsync -av "$PROJECT_DIR/core_v2/Library" "$PKG_DIR/core_v2/"

# 3. Copy Windows Scripts
mkdir -p "$PKG_DIR/windows_scripts"
cp "$PROJECT_DIR/windows_scripts/"*.bat "$PKG_DIR/windows_scripts/"

# 4. Copy Root Config/Files
cp "$PROJECT_DIR/requirements.txt" "$PKG_DIR/"
cp "$PROJECT_DIR/대본.txt" "$PKG_DIR/"
# Include Service Account if present (User requested keys)
if [ -f "$PROJECT_DIR/core_v2/service_account.json" ]; then
    cp "$PROJECT_DIR/core_v2/service_account.json" "$PKG_DIR/core_v2/"
fi

# 5. Create Root Execution Batch (The "One Click" Entry)
# Move the main 99 script to root for easier access
cp "$PKG_DIR/windows_scripts/99_전체_프로세스_통합_실행.bat" "$PKG_DIR/RUN_MOOHYUP_GENERATOR.bat"

# 6. Create instructions
echo "
[설치 및 실행 방법]

1. Python 3.10 이상을 설치하세요. (설치 시 'Add Python to PATH' 체크 필수)
2. 폴더 주소창에 'cmd'를 치고 엔터 -> 터미널 창이 뜨면 아래 명령어 입력:
   pip install -r requirements.txt

3. 준비가 다 되었습니다!
   'RUN_MOOHYUP_GENERATOR.bat' 파일을 더블 클릭하세요.

[주의사항]
- FFmpeg가 설치되어 있어야 합니다. (없다면 https://ffmpeg.org/download.html 에서 다운로드)
- '대본.txt' 내용을 수정하여 원하는 영상을 만드세요.
" > "$PKG_DIR/README.txt"

# 7. Zip
cd "$PROJECT_DIR"
zip -r "TTS_Windows_Pack_Signed.zip" "TTS_Windows_Pack_Signed"

# 8. Move to Downloads
mv "TTS_Windows_Pack_Signed.zip" "$DOWNLOADS_DIR/"

echo "✅ Package created at: $DOWNLOADS_DIR/TTS_Windows_Pack_Signed.zip"
