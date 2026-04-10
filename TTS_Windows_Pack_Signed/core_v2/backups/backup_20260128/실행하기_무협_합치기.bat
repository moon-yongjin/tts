@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [TOOL] 무협 영상 합치기 (Fixed)

set "TARGET_DIR=%USERPROFILE%\Downloads\무협_생성_0127_1440"
set "OUTPUT_FILE=%TARGET_DIR%\무협_최종_합본.mp4"
set "ENGINE_SCRIPT=%~dp0engine\make_concat_list.py"

echo.
echo 📂 대상 폴더: %TARGET_DIR%
echo 📥 결과 파일: %OUTPUT_FILE%
echo.

if not exist "%TARGET_DIR%" (
    echo ❌ 폴더를 찾을 수 없습니다: %TARGET_DIR%
    pause
    goto :EOF
)

echo ⏳ 파일 목록 생성 (Python using Natural Sort)...
py -3.10 "%ENGINE_SCRIPT%" "%TARGET_DIR%"

if errorlevel 1 (
    echo ❌ 목록 생성 실패.
    pause
    goto :EOF
)

pushd "%TARGET_DIR%"
if not exist mylist.txt (
    echo ❌ mylist.txt가 생성되지 않았습니다.
    popd
    pause
    goto :EOF
)

echo.
echo 🚀 병합 시작...
"%USERPROFILE%\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg.exe" -f concat -safe 0 -i mylist.txt -c copy "%OUTPUT_FILE%" -y

if exist "%OUTPUT_FILE%" (
    echo.
    echo ✅ 병합 완료!
    echo 📁 파일 위치: %OUTPUT_FILE%
    del mylist.txt
) else (
    echo ❌ 병합 실패.
)

popd
echo.
echo 작업을 완료하려면 아무 키나 누르세요...
pause > nul
