@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

echo ====================================================
echo 🌐 [무협 생성기] Streamlit Web UI 실행
echo ℹ️ 브라우저가 자동으로 열립니다.
echo ====================================================

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 파이썬이 설치되어 있지 않습니다.
    echo 👉 https://www.python.org/downloads/ 설치해주세요.
    pause
    exit /b
)

:: 2. Install/Update Requirements (Streamlit)
echo.
echo 📦 라이브러리 확인 중...
pip install -r requirements.txt

:: 3. Run Streamlit
echo.
echo 🚀 웹 서버 시작... (창을 닫지 마세요)
echo ----------------------------------------------------
streamlit run app.py

pause
