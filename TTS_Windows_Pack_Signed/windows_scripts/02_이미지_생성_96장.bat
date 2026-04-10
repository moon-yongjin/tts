@echo off
chcp 65001 > nul
echo 🎨 [STEP 02-96장] 96장 고정 이미지 생성을 시작합니다...
echo ※ 이 모드는 대본을 균등하게 96개로 나누어 이미지를 생성합니다.
echo ※ 지침: 인물이 혼자 나오지 않도록 군중이나 대립 장면을 강조합니다.
echo.
py -3.10 core_v2\02_visual_director_96.py
echo.
echo 작업이 완료되었습니다. 창을 닫으려면 아무 키나 누르세요.
pause > nul
