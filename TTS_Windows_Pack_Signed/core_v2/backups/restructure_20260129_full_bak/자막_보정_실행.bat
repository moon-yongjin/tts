@echo off
chcp 65001 > nul
title [자막 보정 도구] 누락된 텍스트 자동 채우기

set "BASE_DIR=%~dp0"
set "FIXER_PATH=%BASE_DIR%engine\srt_final_fixer.py"
set "SCRIPT_PATH=%BASE_DIR%대본.txt"
set "DOWNLOADS=%USERPROFILE%\Downloads"

echo.
echo 🛠️  [자막 보정] 마지막으로 생성된 자막의 누락된 내용을 대본과 대조하여 수정합니다.
echo.

:: 가장 최근 SRT 파일 찾기
for /f "tokens=*" %%F in ('dir "%DOWNLOADS%\*.srt" /b /o-d') do (
    set "LATEST_SRT=%DOWNLOADS%\%%F"
    goto :found
)

echo ❌ 다운로드 폴더에서 자막(.srt) 파일을 찾을 수 없습니다.
pause
exit /b

:found
echo 🔍 대상 자막: %LATEST_SRT%
echo 📄 기준 대본: %SCRIPT_PATH%
echo.

py -3.10 "%FIXER_PATH%" "%LATEST_SRT%" "%SCRIPT_PATH%"

echo.
echo 작업이 끝났습니다. 보정완료 파일이 다운로드 폴더에 생성되었습니다.
pause
