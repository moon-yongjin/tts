#!/bin/bash

# [Web UI Version]
PKG_NAME="Moohyup_WebUI"
PKG_DIR="/Users/a12/Downloads/$PKG_NAME"
PROJECT_DIR="/Users/a12/projects/tts"

echo "📦 [1/4] Preparing Workspace (Web UI)..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

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

# Copy Windows Scripts (Backups mainly, UI replaces them)
mkdir -p "$PKG_DIR/windows_scripts"
cp "$PROJECT_DIR/windows_scripts/"*.bat "$PKG_DIR/windows_scripts/"

# Create requirements.txt (Include Gradio)
cp "$PROJECT_DIR/requirements.txt" "$PKG_DIR/requirements.txt"

# Copy Service Account if exists
if [ -f "$PROJECT_DIR/core_v2/service_account.json" ]; then
    cp "$PROJECT_DIR/core_v2/service_account.json" "$PKG_DIR/core_v2/"
fi

# Inject Keys
echo '{
  "ElevenLabs_API_KEY": "4ac65146a95169cd5530e663dfd89d5b41b05a6d503007f7256861dfc41de97d",
  "Gemini_API_KEY": "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA",
  "Azure_Speech_Key": "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn",
  "Azure_Region": "koreacentral"
}' > "$PKG_DIR/config.json"

# [Web UI Components]
cp "$PROJECT_DIR/app.py" "$PKG_DIR/"
cp "$PROJECT_DIR/RUN_WEBUI.bat" "$PKG_DIR/"
cp "$PROJECT_DIR/launcher.py" "$PKG_DIR/"
cp "$PROJECT_DIR/BUILD_EXE.bat" "$PKG_DIR/"

# Update requirements.txt for Streamlit
echo "streamlit" >> "$PKG_DIR/requirements.txt"

# [Script Input Placeholder]
# Use SCRIPT_INPUT.txt (English Name) + CP949
python3 -c "import codecs; text = open('$PROJECT_DIR/대본.txt', 'r', encoding='utf-8').read(); open('$PKG_DIR/SCRIPT_INPUT.txt', 'w', encoding='cp949', errors='replace').write(text)" 2>/dev/null

echo "✨ [4/4] Compressing..."
cd "/Users/a12/Downloads"
rm -f "Moohyup_WebUI.zip"

zip -r "Moohyup_WebUI.zip" "$PKG_NAME"

echo "✅ Done! /Users/a12/Downloads/Moohyup_WebUI.zip"
