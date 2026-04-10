@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo 🎙️ [AI Voice Direct] 성우 음성 및 자막 생성을 시작합니다...
echo 📄 대본 파일: 대본.txt
echo.

py -3.10 tts_factory.py 대본.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 오류가 발생했습니다. 대본 파일이 있는지, API 키가 맞는지 확인해주세요.
) else (
    echo.
    echo ✨ 음성(.mp3)과 자막(.srt) 생성이 완료되었습니다!
    echo 📂 다운로드(Downloads) 폴더를 확인하세요.
)

echo.
pause
