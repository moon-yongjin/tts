@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 🎙️ 아마존 폴리 공장을 가동합니다...
echo 📄 대본 파일(실행하기폴리대본.txt)을 읽어오는 중...
py -3.10 engine\muhyup_factory.py 실행하기폴리대본.txt
echo.
echo ✅ 모든 작업이 완료되었습니다! 다운로드 폴더를 확인하세요.
pause
