#!/bin/bash
# 01_성우_및_자막_생성.sh
# 아주라(Azure TTS)를 사용하여 전체 나레이션과 자막을 생성합니다.

PYTHON_EXE="/Users/a12/miniforge3/bin/python"
SCRIPT_PATH="/Users/a12/projects/tts/core_v2/01_muhyup_factory_v2.py"

echo "🚀 [STEP 01] 아주라(Azure) 나레이션 및 자막 생성을 시작합니다..."
$PYTHON_EXE $SCRIPT_PATH
echo "✅ 작업이 모두 완료되었습니다."
