@echo off
chcp 65001 > nul
echo --------------------------------------------------
echo 🎨 [STEP 02] 이미지 생성 설정을 시작합니다.
echo --------------------------------------------------
set /p IMG_COUNT="👉 생성할 이미지 수량을 입력하세요 (기본값: 10, 자동 계산: 0): "

echo.
echo 🚀 설정된 수량으로 이미지 생성을 시작합니다...
echo --------------------------------------------------

if "%IMG_COUNT%"=="" set IMG_COUNT=10
python core_v2/02_visual_director_96.py --count %IMG_COUNT%

echo.
echo 작업이 완료되었습니다. 창을 닫으려면 아무 키나 누르세요.
pause > nul
