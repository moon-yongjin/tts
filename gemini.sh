#!/bin/bash
# Gemini CLI 실행 스크립트

# API 키 설정
export GEMINI_API_KEY="AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"

# 로컬 Gemini CLI 실행
# 첫 번째 인자가 있으면 해당 프롬프트로 실행, 없으면 인터랙티브 모드(chat) 실행
if [ -z "$1" ]; then
    ./node_modules/.bin/gemini chat
else
    ./node_modules/.bin/gemini chat "$*"
fi
