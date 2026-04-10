#!/bin/bash
# [전체 프로세스 통합 마스터 스크립트 v3 - Hybrid Edition]
# 개선점: Cloud(Imagen) vs Local(Draw Things) 선택 가능, 시네마틱 그래프 UI 적용

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
echo -e "${GREEN}🚀 [MASTER FLOW v3] 무협 비디오 자동 제작 파이프라인${NC}"
echo "===================================================="

# === 2. 모드 선택 ===
echo -e "\n사용할 이미지 생성 엔진을 선택하세요:"
echo "1) ☁️  Cloud (Google Imagen) - 빠르고 편리함"
echo "2) 🏠 Local (Draw Things / SDXL) - 무료, 고퀄리티, 로컬 제어"
read -p "👉 선택 (1 또는 2): " MODE_CHOICE

if [ "$MODE_CHOICE" == "2" ]; then
    echo -e "${BLUE}✅ [Local Mode] Draw Things / SDXL 엔진을 사용합니다.${NC}"
    GENERATOR_SCRIPT="./02-1_이미지_생성_로컬_진행.sh"
else
    echo -e "${BLUE}✅ [Cloud Mode] Google Imagen 엔진을 사용합니다.${NC}"
    GENERATOR_SCRIPT="./02_이미지_생성_진행.sh"
fi

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
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_part*.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_part*.srt" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_Full_Merged.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_Full_Merged.srt" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*-*.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_배경_효과음_레이어.mp3" -delete || true
echo "✅ 청소 완료."

# STEP 01: 성우 음성 생성
echo -e "\n🎙️ ${GREEN}[STEP 01]${NC} 성우 음성 및 자막 생성..."
STEP_START=$SECONDS
$PYTHON_EXE core_v2/engine/muhyup_factory.py "$SCRIPT_FILE"
echo "⏱️ [STEP 01 완료] 소요: $((SECONDS - STEP_START))초"

# STEP 01-1: 음성 자막 합치기
echo -e "\n🔗 ${GREEN}[STEP 01-1]${NC} 음성/자막 병합..."
STEP_START=$SECONDS
$PYTHON_EXE core_v2/01-1_file_merger.py
echo "⏱️ [STEP 01-1 완료] 소요: $((SECONDS - STEP_START))초"

# 파트 파일 정리
echo "🧹 [CLEANUP] 임시 파트 파일 삭제..."
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_part*.mp3" -delete || true
find "$DOWNLOADS_DIR" -maxdepth 1 -name "*_part*.srt" -delete || true

# STEP 02: 이미지 생성 (선택된 모드)
echo -e "\n🎨 ${GREEN}[STEP 02]${NC} 이미지 생성 파이프라인 가동..."
STEP_START=$SECONDS
bash "$GENERATOR_SCRIPT"
echo "⏱️ [STEP 02 완료] 소요: $((SECONDS - STEP_START))초"

# 검토 및 대기
echo -e "\n----------------------------------------------------"
echo -e "👀 ${GREEN}[검토 단계]${NC} 생성된 이미지를 확인하세요."
echo "📍 위치: Downloads/무협_... 폴더"
echo "----------------------------------------------------"
read -n 1 -s -r -p "👉 다음 단계(영상 변환)로 넘어가려면 아무 키나 누르세요..."
echo -e "\n"

# STEP 03: 시네마틱 빈티지 영상 변환 (New 03-1 V3 Version)
echo -e "\n🎬 ${GREEN}[STEP 03]${NC} 시네마틱 빈티지 영상 변환 (V3 View)..."
STEP_START=$SECONDS
# 03-1 스크립트는 사용자 입력을 받으므로 그대로 실행
$PYTHON_EXE core_v2/03-1_cinematic_v3_vintage.py
echo "⏱️ [STEP 03 완료] 소요: $((SECONDS - STEP_START))초"

# STEP 05: AI SFX & BGM Director (V3-Fixed)
echo -e "\n🎹 ${GREEN}[STEP 05]${NC} AI 지능형 SFX & BGM 배치 (10s/30s)..."
STEP_START=$SECONDS
$PYTHON_EXE core_v2/05-1_ai_sfx_director.py
echo "⏱️ [STEP 05 완료] 소요: $((SECONDS - STEP_START))초"

# STEP 07: 최종 마스터 통합 렌더링 (Video + Multi-Audio)
echo -e "\n🏆 ${GREEN}[STEP 07]${NC} 최종 마스터 렌더링 (다중 오디오 레이어 통합)..."
STEP_START=$SECONDS
$PYTHON_EXE core_v2/07_master_integration.py
echo "⏱️ [STEP 07 완료] 소요: $((SECONDS - STEP_START))초"

# 마무리
echo -e "\n===================================================="
echo -e "${GREEN}✨ [전체 공정 완료]${NC}"
TOTAL_ELAPSED=$((SECONDS - TOTAL_START))
echo "⏱️ 총 소요 시간: $((TOTAL_ELAPSED / 60))분 $((TOTAL_ELAPSED % 60))초"
echo "📂 결과물 위치: Downloads 폴더 확인"
echo "===================================================="
echo ""
read -t 5 -p "5초 후 종료됩니다..." || true
