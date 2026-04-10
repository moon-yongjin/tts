@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo 🎵 [BGM Master] 외부 음악 믹싱을 시작합니다...
py -3.10 engine\BGM_Master.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 오류가 발생했습니다. bgm_plan.json 설정이나 파일명을 확인해주세요.
) else (
    echo.
    echo ✨ 모든 작업이 완료되었습니다! 
    echo 📂 결과물 위치: Library/projects 폴더 내의 프로젝트 폴더
)

pause
