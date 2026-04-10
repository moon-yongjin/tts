@echo off
chcp 65001 > nul
title [STEP 05] AI 배경음 작곡 및 믹싱

echo.
echo 🎶 [Step 05] AI가 대본을 분석하여 분위기에 맞는 배경음을 작곡하고 믹싱합니다...
echo ⏳ Downloads 폴더의 가장 최근 목소리 합본 파일을 자동으로 찾아 작업을 수행합니다.
echo.

py -3.10 core_v2\05_bgm_composer.py

echo.
if errorlevel 1 (
    echo ❌ 작업 중 오류가 발생했습니다. 위 메시지를 확인해 주세요.
) else (
    echo ✨ 모든 작업이 성공적으로 완료되었습니다! 결과물은 Downloads 폴더에서 확인하세요.
)
echo.
pause
