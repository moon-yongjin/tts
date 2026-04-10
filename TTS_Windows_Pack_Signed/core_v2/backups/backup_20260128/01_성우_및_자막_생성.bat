@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [STEP 01] 성우 및 자막 생성기

:: [설정] 스크립트 실행 위치를 기준으로 경로 설정
set "BASE_DIR=%~dp0"
set "ENGINE_SCRIPT=%BASE_DIR%engine\muhyup_factory.py"
set "INPUT_FILE=%BASE_DIR%대본.txt"

echo.
echo ======================================================================
echo 🎙️ [STEP 01] 성우 음성 및 자막(SRT) 생성을 시작합니다...
echo ======================================================================
echo.
echo 📂 작업 경로: %BASE_DIR%
echo 📄 대상 대본: %INPUT_FILE%
echo.

:: [검사] 대본 파일 존재 여부 확인
if not exist "%INPUT_FILE%" (
    echo [오류] '대본.txt' 파일을 찾을 수 없습니다!
    echo 파일을 '%BASE_DIR%' 위치에 넣어주세요.
    echo.
    pause
    exit /b
)

:: [실행] 파이썬 엔진 호출
echo ⏳ AI 성우 생성 엔진 구동 중...
py -3.10 "%ENGINE_SCRIPT%" "%INPUT_FILE%"

if errorlevel 1 (
    echo.
    echo ❌ 작업 중 오류가 발생했습니다.
    echo 위 로그를 확인해주세요.
) else (
    echo.
    echo ✅ 모든 작업이 완료되었습니다!
)

echo.
pause
