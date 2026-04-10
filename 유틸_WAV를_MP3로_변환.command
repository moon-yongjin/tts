#!/bin/bash
# 유틸_WAV를_MP3로_변환.command

# 터미널 창 유지 및 작업 디렉토리 설정
cd "$(dirname "$0")"

DOWNLOADS_DIR="$HOME/Downloads"
FFMPEG_EXE="ffmpeg"

echo "=================================================="
echo "🎵  WAV -> MP3 일괄 변환 유틸리티 시작"
echo "📍 대상 폴더: $DOWNLOADS_DIR"
echo "--------------------------------------------------"

# WAV 파일 목록 가져오기
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
WAV_FILES=$(ls "$DOWNLOADS_DIR"/*.wav 2>/dev/null)

if [ -z "$WAV_FILES" ]; then
    echo "❌ 변환할 .wav 파일이 없습니다."
else
    for wav_path in $WAV_FILES; do
        mp3_path="${wav_path%.wav}.mp3"
        filename=$(basename "$wav_path")
        
        echo "🎙️ 변환 중: $filename"
        
        # FFmpeg로 변환 (192k 비트레이트, 덮어쓰기 허용)
        $FFMPEG_EXE -i "$wav_path" -vn -ar 44100 -ac 2 -b:a 192k -y "$mp3_path" > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ 완료: $(basename "$mp3_path")"
        else
            echo "❌ 실패: $filename"
        fi
    done
fi
IFS=$SAVEIFS

echo "--------------------------------------------------"
echo "✨ 모든 작업이 완료되었습니다."
echo "=================================================="

echo "엔터를 누르면 종료됩니다."
read
