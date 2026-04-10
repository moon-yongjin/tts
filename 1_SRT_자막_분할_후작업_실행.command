#!/bin/bash
echo "🎬 SRT 자막 파일 선택 중..."
# Finder를 통해 파일 선택 팝업 (SRT 파일만 선택 가능)
SELECTED_FILE=$(osascript -e 'POSIX path of (choose file of type {"srt"} with prompt "처리할 SRT 파일을 선택하세요")' 2>/dev/null)

if [ -z "$SELECTED_FILE" ]; then
    echo "❌ 파일 선택이 취소되었습니다. 종료합니다."
    sleep 2
    exit 0
fi

echo "🚀 선택된 파일: $SELECTED_FILE"
echo "🎬 SRT 자막 분할 후작업 가동 중 (8~12자 비례배분)..."
/Users/a12/miniforge3/bin/python /Users/a12/projects/tts/core_v2/04_srt_subsplitter.py "$SELECTED_FILE"
echo "🎉 자막 분할 완료!"
read -p "엔터를 누르면 종료됩니다..."
