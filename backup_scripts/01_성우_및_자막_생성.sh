#!/bin/bash

# [MAC 실행 스크립트]
echo '🎙️ [STEP 01] 성우 음성 및 자막(SRT) 생성을 시작합니다...'
python3 core_v2/engine/muhyup_factory.py 대본.txt
