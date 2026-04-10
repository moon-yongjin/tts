#!/bin/bash
# 02-3_Whisk_이미지_자동생성.command

# 현재 스크립트 위치로 이동
cd "$(dirname "$0")"

# 설정
PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
DIRECTOR_PATH="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/visual_prompt_generator.py"
WHISK_GEN_PATH="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/whisk_gen.py"
DEFAULT_SCRIPT="/Users/a12/projects/tts/대본.txt"
PROMPTS_JSON="visual_prompts.json"

clear
echo "===================================================="
echo "   🚀 Google Whisk AI 비주얼 디렉터 자동화 시스템"
echo "===================================================="
echo ""

# 1. 크롬 실행 여부 확인
if ! lsof -i :9222 > /dev/null; then
    echo "❌ 에러: 원격 제어용 크롬(Port 9222)이 실행 중이지 않습니다."
    echo "💡 먼저 가이드에 따라 크롬을 --remote-debugging-port=9222 옵션으로 켜주세요."
    echo ""
    exit 1
fi

# 2. 대본 파일 확인
if [ ! -f "$DEFAULT_SCRIPT" ]; then
    echo "❌ 에러: 대본 파일을 찾을 수 없습니다. ($DEFAULT_SCRIPT)"
    exit 1
fi

echo ""
echo "🤖 [STEP 1] AI 비주얼 디렉터: 대본 문단(청크)별 자동 분석 시작..."
# --chunk: 대본의 문단 단위로 이미지를 하나씩 생성하도록 분석
$PYTHON_PATH "$DIRECTOR_PATH" --script "$DEFAULT_SCRIPT" --output "$PROMPTS_JSON" --chunk

if [ $? -ne 0 ]; then
    echo "❌ 에러: 프롬프트 생성 중 문제가 발생했습니다."
    exit 1
fi

echo ""
echo "🎨 [STEP 2] Google Whisk: 프롬프트 푸시 시작 (다운로드 없음)..."
# --no-download: 다운로드 생략, --rapid: 생성 대기 없이 즉시 다음 프롬프트 전송
$PYTHON_PATH "$WHISK_GEN_PATH" --prompts-file "$PROMPTS_JSON" --port 9222 --no-download --rapid

echo ""
echo "===================================================="
echo "✅ 모든 작업이 완료되었습니다!"
echo "📂 저장 위치: ~/Downloads/Whisk_Generations"
echo "===================================================="
read -p "잠시 후 창을 닫으려면 [Enter]를 누르세요..."
