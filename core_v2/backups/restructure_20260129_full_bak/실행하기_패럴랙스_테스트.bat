@echo off
chcp 65001 > nul
echo 🖼️ [PARALLAX] Rembg 기반 패럴랙스 애니메이션 테스트를 시작합니다...
echo.
echo * 처음 실행 시 배경 제거용 AI 모델(u2net) 다운로드를 위해 몇 분 정도 걸릴 수 있습니다.
echo.
py -3.10 parallax_effect_v1.py
echo.
echo 작업이 완료되었습니다. parallax_output.mp4 파일을 확인하세요.
pause > nul
