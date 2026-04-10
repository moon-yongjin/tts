#!/bin/bash
# Z-Image Turbo 실행 및 로컬 동기화 툴

# [설정]
REMOTE_IP="203.57.40.175"
REMOTE_PORT="14029"
SSH_KEY="~/.ssh/id_ed25519_runpod"
LOCAL_PORT="18188"  # 로컬 포트는 18188로 설정 (8188 충돌 방지)

echo "🌉 RunPod에 보안 터널(SSH Tunnel)을 연결 중입니다..."
echo "--------------------------------------------------"

# SSH 터널 생성 (백그라운드 실행)
# 로컬 18188 -> 리모트 8188
ssh -f -N -L $LOCAL_PORT:127.0.0.1:8188 -i $SSH_KEY -p $REMOTE_PORT root@$REMOTE_IP

# 터널 연결 대기
sleep 2

echo "🎨 Z-Image Turbo 생성을 시작합니다..."
echo "--------------------------------------------------"

# Python 스크립트 실행 (로컬 python3 사용)
python3 /Users/a12/projects/tts/run_zimage_turbo.py "$@"

# 터널 종료
echo "--------------------------------------------------"
echo "🛑 보안 터널을 해제합니다."
pkill -f "L $LOCAL_PORT:127.0.0.1:8188"

echo "✅ 완료되었습니다. 창을 닫으려면 아무 키나 누르세요."
read -n 1 -s
