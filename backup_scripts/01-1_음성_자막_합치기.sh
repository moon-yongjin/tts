#!/bin/bash

# [MAC 실행 스크립트]
echo ' Running 01-1_음성_자막_합치기 on Mac...'
START_TIME=$SECONDS
python3 core_v2/01-1_file_merger.py

ELAPSED=$((SECONDS - START_TIME))
MIN=$((ELAPSED / 60))
SEC=$((ELAPSED % 60))
echo "⏱️ [STEP 01-1 완료] 소요 시간: ${MIN}분 ${SEC}초"
