#!/bin/bash

# [CONFIG]
POD_USER="root"
POD_IP="213.173.109.153"
POD_PORT="19090"
SSH_KEY_PATH="$HOME/.ssh/id_ed25519_runpod"
REMOTE_OUTPUT_DIR="/workspace/ComfyUI/output"
LOCAL_DOWNLOADS_DIR="$HOME/Downloads"

# [TIMESTAMP]
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BATCH_FOLDER="$LOCAL_DOWNLOADS_DIR/Batch_Scenes_$TIMESTAMP"

echo "📂 로컬 다운로드 폴더 생성: $BATCH_FOLDER"
mkdir -p "$BATCH_FOLDER"

echo "📡 런팟 서버에서 이미지 가져오는 중..."
# 모든 PNG 파일을 가져오도록 패턴 확장 (GGUF, Batch, Manual Output 등 모두 포함)
PATTERN="*.png"

echo "   📦 $PATTERN 파일 다운로드 중..."
scp -P "$POD_PORT" -i "$SSH_KEY_PATH" "$POD_USER@$POD_IP:$REMOTE_OUTPUT_DIR/$PATTERN" "$BATCH_FOLDER/" 2>/dev/null

if [ "$(ls -A "$BATCH_FOLDER")" ]; then
    echo "✅ 다운로드 완료! ($BATCH_FOLDER)"
    
    echo "🗑️ 런팟 서버에서 다운로드된 파일 삭제 중..."
    ssh -p "$POD_PORT" -i "$SSH_KEY_PATH" "$POD_USER@$POD_IP" "rm $REMOTE_OUTPUT_DIR/$PATTERN 2>/dev/null"
    echo "✨ 런팟 서버 정리 완료."
    
    open "$BATCH_FOLDER"
else
    echo "❌ 가져올 파일이 없거나 다운로드에 실패했습니다."
fi
