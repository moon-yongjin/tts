#!/bin/bash
# 50 Popular Fitness & Workout Videos Downloader (5,000+ Likes)
# Created by Antigravity

# 스크립트 실행 위치로 이동
cd "$(dirname "$0")"

# 저장 폴더 생성
mkdir -p downloads/fitness_videos

# yt-dlp 경로 설정
YT_DLP="/opt/homebrew/bin/yt-dlp"

echo "🚀 좋아요 5,000개 이상의 인기 피트니스 영상 50개 다운로드를 시작합니다..."
echo "📂 저장 위치: $(pwd)/downloads/fitness_videos"

# 검색 및 다운로드 실행
# ytsearch500: 500개 후보 검색
# --match-filter: 좋아요 5,000개 이상 & 60초 미만
# --max-downloads 50: 50개 완료 시 종료
$YT_DLP -o "downloads/fitness_videos/%(title)s.%(ext)s" \
--match-filter "like_count >= 5000 & duration < 60" \
--max-downloads 50 \
--ignore-errors \
--no-playlist \
--merge-output-format mp4 \
"ytsearch500:gym motivation shorts fitness"

echo "✅ 모든 다운로드가 완료되었습니다."
read -p "엔터를 누르면 창이 닫힙니다."
