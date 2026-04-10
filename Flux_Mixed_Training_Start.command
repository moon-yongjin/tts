#!/bin/bash
# 🚀 [ Flux Multi-Character LoRA Training Start ]
# Target: 6 AM Training Session (Balanced Drama Characters)

echo "===================================================="
echo "   🎨 Flux 복합 캐릭터 로라 학습 시작 (4인 통합) 🎨"
echo "===================================================="
echo ""

# 1. 경로 설정
KOHYA_ENV="/Users/a12/miniforge3/envs/kohya/bin/python"
ACCELERATE="/Users/a12/miniforge3/envs/kohya/bin/accelerate"
TRAIN_SCRIPT="/Users/a12/projects/tts/kohya_ss/sd-scripts/flux_train_network.py"
CONFIG_FILE="/Users/a12/projects/tts/kohya_ss/training/mixed_characters/train_config.toml"

# 2. 실행 권한 및 환경 체크
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ [에러] 설정 파일을 찾을 수 없습니다: $CONFIG_FILE"
    exit 1
fi

echo "📂 학습 데이터: kohya_ss/training/mixed_characters/image"
echo "⚙️ 설정 파일: mixed_characters/train_config.toml"
echo "🚀 학습을 시작합니다. (Mac 성능에 따라 시간이 소요될 수 있습니다...)"
echo ""

# 3. 학습 실행 (Kohya Flux Network Training)
cd /Users/a12/projects/tts/kohya_ss || exit 1

"$ACCELERATE" launch \
  --num_cpu_threads_per_process 8 \
  "$TRAIN_SCRIPT" \
  --config_file "$CONFIG_FILE"

echo ""
echo "===================================================="
echo "✅ 학습 프로세스가 종료되었습니다."
echo "📍 모델 저장: kohya_ss/training/mixed_characters/model"
echo "===================================================="
read -p "엔터를 누르면 종료합니다..."
