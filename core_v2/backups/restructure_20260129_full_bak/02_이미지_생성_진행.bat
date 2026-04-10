@echo off
chcp 65001 > nul
echo 🎨 [STEP 02-V2] 배경 강화 이미지 생성을 시작합니다...
echo ※ 스타일을 선택하지 않으면 기본값으로 진행됩니다.
echo 🌿 이 버전은 대본에 따른 배경 변화와 일관성을 더 세밀하게 묘사합니다.
echo.
py -3.10 visual_director_v2.py
echo.
echo 작업이 완료되었습니다. 창을 닫으려면 아무 키나 누르세요.
pause > nul
