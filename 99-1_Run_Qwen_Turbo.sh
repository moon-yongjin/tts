#!/bin/bash
# Qwen TTS Turbo 실행 및 모니터링 툴

# [설정] - 현재 Pod 정보 (157.157.221.29:22404)
REMOTE_IP="157.157.221.29"
REMOTE_PORT="22404"
SSH_KEY="~/.ssh/id_ed25519_runpod"
GOOGLE_API_KEY="AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"

echo "🚀 Qwen-TTS [Batch Turbo] 엔진에 접속 중입니다..."
echo "--------------------------------------------------"

# SSH 접속 및 실행 (실시간 로그 출력)
ssh -o StrictHostKeyChecking=accept-new -i $SSH_KEY -p $REMOTE_PORT root@$REMOTE_IP \
"export GOOGLE_API_KEY='$GOOGLE_API_KEY' && \
 export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True && \
 python3 /workspace/Qwen3-TTS/run_turbo_qwen_sohee.py /workspace/대본.txt"

echo "--------------------------------------------------"
echo "📥 생성이 완료되었습니다! 파일을 자동으로 다운로드합니다..."

# 로컬 다운로드 폴더 준비
LOCAL_DOWNLOAD_DIR="$HOME/Downloads/Qwen_TTS_Output"
mkdir -p "$LOCAL_DOWNLOAD_DIR"

# 최신 파일 다운로드 (파츠 및 최종 병합 파일)
scp -i $SSH_KEY -P $REMOTE_PORT -r "root@$REMOTE_IP:/workspace/Downloads/Turbo_Qwen_*" "$LOCAL_DOWNLOAD_DIR/"
scp -i $SSH_KEY -P $REMOTE_PORT -r "root@$REMOTE_IP:/workspace/Downloads/Part_*" "$LOCAL_DOWNLOAD_DIR/"
scp -i $SSH_KEY -P $REMOTE_PORT -r "root@$REMOTE_IP:/workspace/Downloads/Final_*" "$LOCAL_DOWNLOAD_DIR/"

echo "--------------------------------------------------"
echo "✅ 모든 파일이 $LOCAL_DOWNLOAD_DIR 에 저장되었습니다."
echo "✨ 창을 닫으려면 아무 키나 누르세요."
read -n 1 -s
