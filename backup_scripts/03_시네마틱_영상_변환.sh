#!/bin/bash

# [MAC 실행 스크립트]
echo '🎬 [STEP 03] 이미지를 고퀄리티 시네마틱 V2 영상으로 변환합니다...'
START_TIME=$SECONDS
python3 core_v2/03_video_director_v2.py

ELAPSED=$((SECONDS - START_TIME))
MIN=$((ELAPSED / 60))
SEC=$((ELAPSED % 60))
echo "⏱️ [STEP 03 완료] 소요 시간: ${MIN}분 ${SEC}초"
