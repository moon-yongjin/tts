#!/bin/bash
# 02-3_V5_수채화_이미지_생성.command

# 현재 스크립트 위치로 이동
cd "$(dirname "$0")"

# 설정
PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
DIRECTOR_PY="utils/youtube/lib/v5_watercolor_scenario_gen.py"
WHISK_GEN_PY="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/whisk_gen.py"
TRANSCRIPT_PATH="/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_Pinpoint_Visual_Hardship_Transcript.txt"
PROMPTS_JSON="watercolor_prompts.json"

clear
echo "===================================================="
echo "   🎨 V5 수채화 시나리오 디렉터 (Whisk 통합)"
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
if [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "⚠️ 경고: 기본 대본을 찾을 수 없습니다. ($TRANSCRIPT_PATH)"
    read -p "대본 파일 경로를 직접 입력하세요: " TRANSCRIPT_PATH
fi

echo "❓ 몇 개의 장면을 수채화로 생성할까요?"
read -p "입력 (기본값: 10): " NUM_SCENES
if [ -z "$NUM_SCENES" ]; then NUM_SCENES=10; fi

# 3. 프롬프트 생성
echo ""
echo "🤖 [STEP 1] AI 시각적 디렉터: 거친 수채화 장면 분석 시작..."
$PYTHON_PATH "$DIRECTOR_PY" --script "$TRANSCRIPT_PATH" --output "$PROMPTS_JSON" --num "$NUM_SCENES"

if [ $? -ne 0 ]; then
    echo "❌ 에러: 프롬프트 생성 중 문제가 발생했습니다."
    exit 1
fi

echo ""
echo "===================================================="
echo "📝 프롬프트가 생성되었습니다: $PROMPTS_JSON"
echo "💡 파일을 열어 내용을 수정하거나 더 추가하실 수 있습니다."
echo "===================================================="
read -p "이미지 생성을 시작하시겠습니까? (y/n): " PROCEED

if [[ "$PROCEED" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 [STEP 2] Google Whisk: 초고속 '래피드 파이어' 연사 시작 (3레퍼런스 풀가동)..."
    $PYTHON_PATH "$WHISK_GEN_PY" --prompts-file "$PROMPTS_JSON" --port 9222 --no-download --rapid
else
    echo "👋 작업을 종료합니다. 프롬프트 파일은 보존됩니다."
fi

echo ""
echo "===================================================="
echo "✅ 모든 작업이 완료되었습니다!"
echo "📂 저장 위치: ~/Downloads/Whisk_Generations"
echo "===================================================="
read -p "잠시 후 창을 닫으려면 [Enter]를 누르세요..."
