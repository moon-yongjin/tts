@echo off
chcp 65001 > nul
echo 👦 [FACE-TRACK] MediaPipe 기반 얼굴 인식 및 목 중심 까딱임 테스트...
echo.
py -3.10 face_animation_v1.py
echo.
echo 작업이 완료되었습니다. face_tracked_output.mp4 파일을 확인하세요.
pause > nul
