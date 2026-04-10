#!/bin/bash

# Configuration
PROJECT_DIR="/Users/a12/projects/tts"
VENV_PATH="$PROJECT_DIR/venv_dt"
PYTHON_SCRIPT="$PROJECT_DIR/batch_generate_dt.py"

echo "🎨 [Draw Things Automation] 80년대 필름 스타일 생성 시작..."

# 1. 드로띵 앱 실행 확인 (백그라운드)
if ! pgrep -x "Draw Things" > /dev/null; then
    echo "🚀 드로띵 앱이 꺼져 있어 백그라운드에서 조용히 실행합니다..."
    open -g -a "Draw Things"
    # 앱 로딩 대기
    sleep 8
fi

# 2. API 서버 응답 대기
echo "⏳ API 서버 연결 확인 중 (127.0.0.1:7860)..."
COUNTER=0
while ! curl -s http://127.0.0.1:7860/sdapi/v1/options > /dev/null; do
    sleep 2
    COUNTER=$((COUNTER+1))
    if [ $COUNTER -gt 15 ]; then
        echo "❌ [에러] 드로띵 서버가 응답하지 않습니다."
        echo "앱 설정에서 [File] -> [HTTP API Server] -> [Start]가 되어 있는지 확인해주세요."
        exit 1
    fi
done

echo "✅ 서버 연결 성공!"

# 3. 파이썬 배치 스크립트 실행
# 인자가 없으면 기본 10장 생성
COUNT=${1:-10}

echo "🚀 총 $COUNT장의 이미지를 생성합니다 (8비트 최적화 세팅)..."
"$VENV_PATH/bin/python" "$PYTHON_SCRIPT" "$COUNT"

echo "✨ 모든 작업이 완료되었습니다! (결과물: Downloads/Script_Scenes_Dynamic)"
