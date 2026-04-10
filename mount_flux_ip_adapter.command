#!/bin/bash

# 설정
PYTHON_PATH="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
TARGET_DIR="/Users/a12/Library/Containers/com.liuliu.draw-things/Data/Documents/Models/controlnet/flux-ip-adapter"

echo "=============================================="
echo "🔌 Flux IP-Adapter 장착 (다운로드 & 설정)"
echo "=============================================="
echo "경로: $TARGET_DIR"

# 폴더 생성
mkdir -p "$TARGET_DIR"

# 다운로드 실행
echo "⬇️  XLabs-AI/flux-ip-adapter 다운로드 시작..."
"$PYTHON_PATH" -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='XLabs-AI/flux-ip-adapter', local_dir='$TARGET_DIR')"

if [ $? -eq 0 ]; then
    echo "✅ 다운로드 완료!"
    echo "이제 Draw Things 앱에서 ControlNet 모델로 불러올 수 있습니다."
else
    echo "❌ 다운로드 실패. 네트워크 상태를 확인해주세요."
fi

# 종료 대기
echo "엔터를 누르면 종료됩니다."
read
