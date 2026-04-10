@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 1. 폴더 경로 설정
set "script_dir=%~dp0"
cd /d "%script_dir%"

echo.
echo ======================================================
echo    🎥 AI 비디오 생성 전용 배치 (5.7초 리듬 모션)
echo ======================================================
echo.
echo ※ 다운로드 폴더의 가장 최신 '무협_생성' 폴더 이미지를 변환합니다.
echo.

:: 2. 파이썬 스크립트 실행
py -3.10 video_director_standalone.py

echo.
echo ======================================================
echo    ✨ 비디오 생성 작업이 완료되었습니다.
echo ======================================================
pause
