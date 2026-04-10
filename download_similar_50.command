#!/bin/bash
# 50 Gardening & Backyard Transformation Videos Downloader
# Created by Antigravity

# 스크립트 실행 위치로 이동
cd "$(dirname "$0")"

# 저장 폴더 생성
mkdir -p downloads/similar_videos

# yt-dlp 경로 설정
YT_DLP="/opt/homebrew/bin/yt-dlp"

echo "🚀 50개의 유사 영상 다운로드를 시작합니다..."
echo "📂 저장 위치: $(pwd)/downloads/similar_videos"

# 다운로드 실행 (40 TikTok + 10 YouTube Shorts)
$YT_DLP -o "downloads/similar_videos/%(title)s.%(ext)s" \
--merge-output-format mp4 \
--ignore-errors \
--no-playlist \
"https://www.tiktok.com/@plants.and.garden/video/7625554576388803843" \
"https://www.tiktok.com/@plants.and.garden/video/7625064515704605955" \
"https://www.tiktok.com/@plants.and.garden/video/7624397258045312278" \
"https://www.tiktok.com/@plants.and.garden/video/7624263313093823766" \
"https://www.tiktok.com/@plants.and.garden/video/7623660346691161366" \
"https://www.tiktok.com/@plants.and.garden/video/7622666827977723158" \
"https://www.tiktok.com/@plants.and.garden/video/7622582787148696854" \
"https://www.tiktok.com/@plants.and.garden/video/7621963961319050499" \
"https://www.tiktok.com/@plants.and.garden/video/7621854650278350102" \
"https://www.tiktok.com/@plants.and.garden/video/7621539930786811158" \
"https://www.tiktok.com/@plants.and.garden/video/7621209330582342934" \
"https://www.tiktok.com/@plants.and.garden/video/7621132041127546134" \
"https://www.tiktok.com/@plants.and.garden/video/7620393266462215446" \
"https://www.tiktok.com/@plants.and.garden/video/7620337371535379734" \
"https://www.tiktok.com/@plants.and.garden/video/7620185403823312150" \
"https://www.tiktok.com/@plants.and.garden/video/7620086071094742294" \
"https://www.tiktok.com/@plants.and.garden/video/7619859833574919446" \
"https://www.tiktok.com/@plants.and.garden/video/7619787498075524374" \
"https://www.tiktok.com/@plants.and.garden/video/7619294172658289942" \
"https://www.tiktok.com/@plants.and.garden/video/7618846213936368918" \
"https://www.tiktok.com/@plants.and.garden/video/7618330219505831190" \
"https://www.tiktok.com/@plants.and.garden/video/7618152650361556246" \
"https://www.tiktok.com/@plants.and.garden/video/7617945603183529238" \
"https://www.tiktok.com/@plants.and.garden/video/7617832733061958934" \
"https://www.tiktok.com/@plants.and.garden/video/7617215603333516566" \
"https://www.tiktok.com/@plants.and.garden/video/7617133981116534038" \
"https://www.tiktok.com/@plants.and.garden/video/7616995549488647446" \
"https://www.tiktok.com/@plants.and.garden/video/7616662982109515030" \
"https://www.tiktok.com/@plants.and.garden/video/7616408740539026710" \
"https://www.tiktok.com/@plants.and.garden/video/7616356675850784003" \
"https://www.tiktok.com/@plants.and.garden/video/7616287049989000470" \
"https://www.tiktok.com/@plants.and.garden/video/7615923904472714518" \
"https://www.tiktok.com/@plants.and.garden/video/7615692181076053271" \
"https://www.tiktok.com/@plants.and.garden/video/7615658372401990934" \
"https://www.tiktok.com/@plants.and.garden/video/7615520196865903894" \
"https://www.tiktok.com/@plants.and.garden/video/7615273595941555478" \
"https://www.tiktok.com/@plants.and.garden/video/7615248212420660482" \
"https://www.tiktok.com/@plants.and.garden/video/7615216984115907862" \
"https://www.tiktok.com/@plants.and.garden/video/7614639966836083990" \
"https://www.tiktok.com/@plants.and.garden/video/7614616010162785558" \
"https://www.youtube.com/shorts/MyY5BZxgqFU" \
"https://www.youtube.com/shorts/XmKUjhdGr4s" \
"https://www.youtube.com/shorts/lb4dfhcriqc" \
"https://www.youtube.com/shorts/xpoZ0kOFbhE" \
"https://www.youtube.com/shorts/TetumVP8RBE" \
"https://www.youtube.com/shorts/JHT7tTHx1gM" \
"https://www.youtube.com/shorts/WTAE2inTE8Y" \
"https://www.youtube.com/shorts/M4Utms7Iaag" \
"https://www.youtube.com/shorts/_y8B8voK1PA" \
"https://www.youtube.com/shorts/-oP6zLskTzs"

echo "✅ 모든 다운로드가 완료되었습니다."
read -p "엔터를 누르면 창이 닫힙니다."
