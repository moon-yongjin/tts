@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [STEP] ê°„ë‹¨ ?ìƒ ?¸ì§‘
echo [STEP] ê°„ë‹¨ ?ìƒ ?¸ì§‘???œì‘?©ë‹ˆ??..

set "SCRIPT=?€ë³?txt"
set "AUDIO=%USERPROFILE%\Downloads\?€ë³?part1.mp3"
set "SUBTITLE=%USERPROFILE%\Downloads\?€ë³?part1.srt"
set "OUTPUT=%USERPROFILE%\Downloads\?¸ì§‘???ìƒ.mp4"

:: ?´ë?ì§€ ?ëŠ” ?ìƒ ?Œì¼???ˆëŠ”ì§€ ?•ì¸
set "MEDIA_FILE="
if exist "media\input_video.mp4" set "MEDIA_FILE=media\input_video.mp4"
if exist "media\input_image.jpg" set "MEDIA_FILE=media\input_image.jpg"
if exist "media\input_image.png" set "MEDIA_FILE=media\input_image.png"

if not defined MEDIA_FILE (
    echo ë¯¸ë””???Œì¼??ì°¾ì„ ???†ìŠµ?ˆë‹¤. media ?´ë”??input_video.mp4, input_image.jpg ?ëŠ” input_image.png ?Œì¼???£ì–´ì£¼ì„¸??
    pause
    exit /b
)

:: FFmpeg ëª…ë ¹???¤í–‰
echo FFmpegë¥??¬ìš©?˜ì—¬ ?ìƒ???¸ì§‘ ì¤‘ì…?ˆë‹¤...
ffmpeg -i "%MEDIA_FILE%" -i "%AUDIO%" -vf subtitles="%SUBTITLE%" -c:v libx264 -c:a aac -strict experimental "%OUTPUT%"

if errorlevel 1 (
    echo ?ìƒ ?¸ì§‘ ì¤??¤ë¥˜ê°€ ë°œìƒ?ˆìŠµ?ˆë‹¤.
) else (
    echo ?ìƒ ?¸ì§‘???„ë£Œ?˜ì—ˆ?µë‹ˆ?? ê²°ê³¼ ?Œì¼: %OUTPUT%
)

pause
