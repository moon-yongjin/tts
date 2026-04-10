#!/bin/bash

# [MAC 실행 스크립트]
echo '🎨 [STEP 02-96장] 96장 고정 이미지 생성을 시작합니다...'
START_TIME=$SECONDS
python3 core_v2/02_visual_director_96.py

ELAPSED=$((SECONDS - START_TIME))
MIN=$((ELAPSED / 60))
SEC=$((ELAPSED % 60))
echo "⏱️ [STEP 02 완료] 소요 시간: ${MIN}분 ${SEC}초"
