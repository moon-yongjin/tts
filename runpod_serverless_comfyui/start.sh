#!/bin/bash
set -e

COMFY_DIR="/workspace/runpod-slim/ComfyUI"
CUSTOM_NODES_DIR="${COMFY_DIR}/custom_nodes"

# Z-Image Turbo 커스텀 노드 설치 (없으면 자동 설치)
echo "ZImagePowerNodes 설치 확인 중..."
if [ ! -d "${CUSTOM_NODES_DIR}/ZImagePowerNodes" ]; then
    echo "ZImagePowerNodes 설치 중 (최초 1회)..."
    git clone --depth 1 https://github.com/ZImageAI/ZImagePowerNodes "${CUSTOM_NODES_DIR}/ZImagePowerNodes"
    echo "ZImagePowerNodes 설치 완료!"
else
    echo "ZImagePowerNodes 이미 설치됨. 건너뜀."
fi

echo "ComfyUI 백그라운드 시작..."
cd ${COMFY_DIR}
.venv-cu128/bin/python main.py --listen 127.0.0.1 --port 8188 --highvram > /var/log/comfyui.log 2>&1 &

echo "ComfyUI 시작 대기 중..."
sleep 10

echo "RunPod 서버리스 API 핸들러 시작..."
cd /
python3 -u handler.py
