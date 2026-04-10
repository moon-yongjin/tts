@echo off
chcp 65001 > nul
echo 🎞️ [KEYFRAME] 배경 중심 키프레임 패럴랙스 테스트를 시작합니다...
echo.
py -3.10 parallax_effect_v3.py
echo.
echo 작업이 완료되었습니다. parallax_output_v3.mp4 파일을 확인하세요.
pause > nul
