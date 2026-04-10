#!/bin/bash

# [MAC 실행 스크립트]
echo '🎵 [STEP 04] 영상에 어울리는 BGM과 SFX를 합성합니다...'
START_TIME=$SECONDS
python3 core_v2/04_bgm_master.py

ELAPSED=$((SECONDS - START_TIME))
MIN=$((ELAPSED / 60))
SEC=$((ELAPSED % 60))
echo "⏱️ [STEP 04 완료] 소요 시간: ${MIN}분 ${SEC}초"
