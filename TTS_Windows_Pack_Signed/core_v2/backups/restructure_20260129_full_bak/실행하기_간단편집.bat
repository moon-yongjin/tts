@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [STEP] 간단 영상 편집
echo [STEP] 간단 영상 편집을 시작합니다...

set "SCRIPT=대본.txt"
set "AUDIO=%USERPROFILE%\Downloads\대본_part1.mp3"
set "SUBTITLE=%USERPROFILE%\Downloads\대본_part1.srt"
set "OUTPUT=%USERPROFILE%\Downloads\편집된_영상.mp4"

:: 이미지 또는 영상 파일이 있는지 확인
set "MEDIA_FILE="
if exist "media\input_video.mp4" set "MEDIA_FILE=media\input_video.mp4"
if exist "media\input_image.jpg" set "MEDIA_FILE=media\input_image.jpg"
if exist "media\input_image.png" set "MEDIA_FILE=media\input_image.png"

if not defined MEDIA_FILE (
    echo 미디어 파일을 찾을 수 없습니다. media 폴더에 input_video.mp4, input_image.jpg 또는 input_image.png 파일을 넣어주세요.
    pause
    exit /b
)

:: FFmpeg 명령어 실행
echo FFmpeg를 사용하여 영상을 편집 중입니다...
ffmpeg -i "%MEDIA_FILE%" -i "%AUDIO%" -vf subtitles="%SUBTITLE%" -c:v libx264 -c:a aac -strict experimental "%OUTPUT%"

if errorlevel 1 (
    echo 영상 편집 중 오류가 발생했습니다.
) else (
    echo 영상 편집이 완료되었습니다. 결과 파일: %OUTPUT%
)

pause