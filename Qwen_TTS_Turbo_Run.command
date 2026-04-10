#!/bin/bash
# Qwen TTS Turbo 실행 및 모니터링 툴 (목소리 선택 기능 추가)

# [설정]
REMOTE_IP="203.57.40.175"
REMOTE_PORT="14029"
SSH_KEY="~/.ssh/id_ed25519_runpod"
GOOGLE_API_KEY="AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"

clear
echo "🎙️ Qwen-TTS [Multi-Voice Batch Turbo] 엔진"
echo "--------------------------------------------------"
echo "사용하실 목소리를 선택해 주세요:"
echo "1) 소희 (Sohee) - 비극적, 숨소리 섞인, 애절한 톤"
echo "2) 세레나 (Serena) - 따뜻하고 풍부한, 감성적인 톤"
echo "3) 지원 (Jiwon) - 차분하고 지적인, 냉철한 톤"
echo "--------------------------------------------------"
read -p "번호를 입력하세요 (1-3): " CHOICE

case $CHOICE in
    1) SCRIPT_NAME="run_turbo_qwen_sohee.py"; VOICE_NAME="소희 (Sohee)";;
    2) SCRIPT_NAME="run_turbo_qwen_serena.py"; VOICE_NAME="세레나 (Serena)";;
    3) SCRIPT_NAME="run_turbo_qwen_jiwon.py"; VOICE_NAME="지원 (Jiwon)";;
    *) echo "❌ 잘못된 입력입니다. 종료합니다."; exit 1;;
esac

echo "🚀 $VOICE_NAME 엔진으로 접속 중입니다..."
echo "--------------------------------------------------"

# SSH 접속 및 실행
ssh -o StrictHostKeyChecking=accept-new -i $SSH_KEY -p $REMOTE_PORT root@$REMOTE_IP \
"export GOOGLE_API_KEY='$GOOGLE_API_KEY' && \
 export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True && \
 python3 /workspace/Qwen3-TTS/$SCRIPT_NAME /workspace/대본.txt"

echo "--------------------------------------------------"
echo "📥 생성이 완료되었습니다! 파일을 자동으로 다운로드합니다..."

# 로컬 다운로드 폴더 준비
LOCAL_DOWNLOAD_DIR="$HOME/Downloads/Qwen_TTS_Output"
mkdir -p "$LOCAL_DOWNLOAD_DIR"

# 최신 파일 다운로드 (병합된 최종 파일만 다운로드하여 속도 향상)
echo "--------------------------------------------------"
echo "📥 병합된 최종 파일을 다운로드합니다..."

# 로컬 다운로드 폴더 준비
LOCAL_DOWNLOAD_DIR="$HOME/Downloads/Qwen_TTS_Output"
mkdir -p "$LOCAL_DOWNLOAD_DIR"

# 'Part_*' (쪼개진 파일들)은 제외하고 'Final_*' (합본)만 다운로드
# -p 옵션을 추가하여 가장 최근 생성된 파일들 위주로 가져오도록 유도하거나, 
# 필요하다면 원격 서버의 구버전 파일을 정리하는 로직을 고려할 수 있습니다.
scp -i $SSH_KEY -P $REMOTE_PORT "root@$REMOTE_IP:/workspace/Downloads/Final_*" "$LOCAL_DOWNLOAD_DIR/"

echo "--------------------------------------------------"
echo "✅ 합본 파일이 $LOCAL_DOWNLOAD_DIR 에 저장되었습니다."
echo "✨ 창을 닫으려면 아무 키나 누르세요."
read -n 1 -s
