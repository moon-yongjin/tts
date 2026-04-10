#!/bin/bash
# [전체 프로세스 통합 마스터 스크립트 v99-4 - 다이어리 전용 Edition]
# 특징: 하이브리드 성우 (나레이션: 아주라 / 대사: 소희) + 10초당 1장 이미지
# 부모님께 전하는 감동적인 이야기를 위한 최적화 버전

set -e # 에러 발생 시 즉시 중단
cd "$(dirname "$0")"

# === 1. 환경 및 경로 설정 ===
PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"
DOWNLOADS_DIR="$HOME/Downloads"
SCRIPT_FILE="대본.txt"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "===================================================="
echo -e "${GREEN}🚀 [MASTER FLOW v99-4] 다이어리 전용 파이프라인${NC}"
echo -e "${BLUE}📍 해설: 아주라 (JiMin) / 대사: 제미나이 (Gemini) / 이미지: 10초당 1장${NC}"
echo "===================================================="

# === 2. 모드 및 스크립트 설정 ===
GENERATOR_SCRIPT="./02-1_이미지_생성_진행_다이어리.sh"
CONVERTER_SCRIPT="./03-2_시네마틱_영상_변환_세로.sh"
SFX_SCRIPT="./05-2_AI_효과음_전용_배치.sh"
TTS_ENGINE_SCRIPT="core_v2/01-17_muhyup_factory_azure_gemini.py"

TOTAL_START=$SECONDS

# 에러 트랩
trap 'echo -e "\n${RED}❌ 작업 중 오류가 발생하여 프로세스가 중단되었습니다.${NC}"; exit 1' ERR

# === 3. 입력 파일 검증 ===
if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}❌ 오류: '$SCRIPT_FILE' 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi
echo "✅ 입력 파일 확인 완료: $SCRIPT_FILE"

# === 4. 공정 실행 ===

# STEP 00: 사전 정리
echo -e "\n🧹 ${GREEN}[STEP 00]${NC} 작업 공간 정리 중..."
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_Full_Merged.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_Full_Merged.srt" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "대본_Azure+Sohee_*.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "대본_Azure+Sohee_*.srt" -delete || true
echo "✅ 청소 완료."

# STEP 01: 하이브리드 성우 음성 및 자막 생성 (아주라 + 제미나이)
echo -e "\n🎙️ ${GREEN}[STEP 01]${NC} 하이브리드 성우(Azure + Gemini) 음성/자막 생성..."
STEP_START=$SECONDS
$PYTHON_EXE "$TTS_ENGINE_SCRIPT" "$SCRIPT_FILE"

# 생성된 파일을 후속 공정(STEP 02~)이 인식할 수 있도록 이름 변경 (_Full_Merged 패턴)
echo "🔗 [파일 브릿지] 호환성을 위해 파일명을 변경합니다..."
LATEST_MP3=$(ls -t "$DOWNLOADS_DIR"/대본_*.mp3 2>/dev/null | head -n 1)
LATEST_SRT=$(ls -t "$DOWNLOADS_DIR"/대본_*.srt 2>/dev/null | head -n 1)

if [ -f "$LATEST_MP3" ] && [ -f "$LATEST_SRT" ]; then
    cp "$LATEST_MP3" "$DOWNLOADS_DIR/대본_Full_Merged.mp3"
    cp "$LATEST_SRT" "$DOWNLOADS_DIR/대본_Full_Merged.srt"
    echo "✅ 브릿지 연결 완료: 대본_Full_Merged.mp3/srt 생성됨"
else
    echo -e "${RED}❌ 오류: 생성된 음성 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

echo "⏱️ [STEP 01 완료] 소요: $((SECONDS - STEP_START))초"

# 생성할 이미지 수량 입력 받기
echo -e "\n🎨 생성할 이미지 수량을 입력하세요"
echo -e "👉 엔터 치면 ${BLUE}[자동]${NC} (음성 10초당 1장)으로 진행됩니다."
read -t 10 -p "👉 입력 (숫자 또는 Enter): " USER_IMG_COUNT || USER_IMG_COUNT=""

if [ -z "$USER_IMG_COUNT" ]; then
    echo -e "✅ ${BLUE}[자동 모드]${NC} 음성 길이에 맞춰 최적 수량으로 생성합니다.\n"
    USER_IMG_COUNT="AUTO"
else
    echo -e "✅ 이미지 수량 ${USER_IMG_COUNT}장으로 설정됨.\n"
fi

# STEP 02: 이미지 생성
echo -e "\n🎨 ${GREEN}[STEP 02]${NC} 이미지 생성 파이프라인 가동..."
STEP_START=$SECONDS
bash "$GENERATOR_SCRIPT" "$USER_IMG_COUNT"
echo "⏱️ [STEP 02 완료] 소요: $((SECONDS - STEP_START))초"

# [자동 승인] 검토 단계 스킵하여 다음 단계 가동
echo -e "\n----------------------------------------------------"
echo -e "🚀 이미지 검토 완료 (자동) -> 영상 변환 단계로 진입합니다."
echo "----------------------------------------------------"
echo -e "\n"

# STEP 03: 시네마틱 영상 변환
echo -e "\n🎬 ${GREEN}[STEP 03]${NC} 시네마틱 영상 변환..."
STEP_START=$SECONDS
bash "$CONVERTER_SCRIPT"
echo "⏱️ [STEP 03 완료] 소요: $((SECONDS - STEP_START))초"

# STEP 05: AI SFX Director
echo -e "\n🎹 ${GREEN}[STEP 05]${NC} AI 지능형 SFX & BGM 배치..."
STEP_START=$SECONDS
bash "$SFX_SCRIPT"
echo "⏱️ [STEP 05 완료] 소요: $((SECONDS - STEP_START))초"

# STEP 07: 최종 마스터 통합 렌더링
echo -e "\n🏆 ${GREEN}[STEP 07]${NC} 최종 마스터 렌더링..."
STEP_START=$SECONDS
$PYTHON_EXE core_v2/07_master_integration.py
echo "⏱️ [STEP 07 완료] 소요: $((SECONDS - STEP_START))초"

# 마무리
echo -e "\n===================================================="
echo -e "${GREEN}✨ [전체 공정 완료 - 다이어리 전용 Mode]${NC}"
TOTAL_ELAPSED=$((SECONDS - TOTAL_START))
echo "⏱️ 총 소요 시간: $((TOTAL_ELAPSED / 60))분 $((TOTAL_ELAPSED % 60))초"
echo "📂 결과물 위치: Downloads 폴더 확인"
echo "===================================================="
echo ""
read -t 5 -p "5초 후 종료됩니다..." || true
