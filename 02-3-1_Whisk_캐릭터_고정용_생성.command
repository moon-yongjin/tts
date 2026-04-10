#!/bin/bash

# 설정
PYTHON_PATH="/Users/a12/miniforge3/bin/python3"
DEFAULT_SCRIPT="/Users/a12/projects/tts/대본.txt"
REF_GEN_PATH="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/character_ref_generator.py"
WHISK_GEN_PATH="/Users/a12/.openclaw/skills/whisk-image-gen/scripts/whisk_gen.py"
PROMPTS_JSON="reference_prompts.json"

echo "===================================================="
echo "   👤 02-3-1 Whisk 캐릭터 & 배경 레퍼런스 설정"
echo "===================================================="

# 1. 크롬 연결 확인
lsof -i :9222 > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ 에러: 9222 포트의 크롬을 찾을 수 없습니다."
    echo "명령어: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222"
    exit 1
fi

# 2. 대본 확인
if [ ! -f "$DEFAULT_SCRIPT" ]; then
    echo "❌ 에러: 대본 파일이 없습니다. ($DEFAULT_SCRIPT)"
    exit 1
fi

echo "🤖 [STEP 1] 대본 분석: 주요 캐릭터와 배경 추출 중..."
$PYTHON_PATH "$REF_GEN_PATH" --script "$DEFAULT_SCRIPT" --output "$PROMPTS_JSON"

if [ $? -ne 0 ]; then
    echo "❌ 에러: 분석 실패"
    exit 1
fi

echo ""
echo "🎨 [STEP 2] Whisk 생성: 프롬프트 푸시 시작 (다운로드 없음)..."
# --no-download: 다운로드 생략, --rapid: 생성 대기 없이 즉시 다음 프롬프트 전송
$PYTHON_PATH "$WHISK_GEN_PATH" --prompts-file "$PROMPTS_JSON" --port 9222 --no-download --rapid

echo ""
echo "===================================================="
echo "✅ 캐릭터/배경 레퍼런스(6각도 얼굴 포함) 생성이 완료되었습니다!"
echo "📍 브라우저에서 가장 마음에 드는 캐릭터 사진들을 확인하세요."
echo "📍 그 사진들을 Character Reference로 고정(Pin)한 뒤,"
echo "📍 02-3번을 실행하여 전체 장면을 생성하세요."
echo "===================================================="
