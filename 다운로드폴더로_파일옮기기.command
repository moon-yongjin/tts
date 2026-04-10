#!/bin/bash
# 이 스크립트는 생성된 BGM 샘플을 국장님의 맥 다운로드 폴더로 이동시킵니다.
SOURCE="/Users/a12/projects/tts/downloads/무협_대서사시_BGM_샘플.flac"
TARGET="$HOME/Downloads/무협_대서사시_BGM_샘플.flac"

if [ -f "$SOURCE" ]; then
    cp "$SOURCE" "$TARGET"
    echo "===================================================="
    echo "✅ 복사 완료: $TARGET"
    echo "===================================================="
    # 폴더 열기
    open -R "$TARGET"
else
    echo "❌ 원본 파일을 찾을 수 없습니다: $SOURCE"
fi
