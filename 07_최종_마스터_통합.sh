#!/bin/bash
# [07 최종 마스터 통합 렌더링]
cd "$(dirname "$0")"

PYTHON_EXE="/Users/a12/projects/tts/ComfyUI/venv_312/bin/python"

echo "🏆 [STEP 07] 최종 마스터 통합 렌더링을 시작합니다..."
"$PYTHON_EXE" core_v2/07_master_integration.py
cat /Users/a12/projects/tts/core_v2/07_master_integration.py