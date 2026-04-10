@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

echo ====================================================
echo 🛠️ [무협 생성기] EXE 실행 파일 만들기
echo ℹ️ Python이 설치되어 있어야 합니다.
echo ====================================================

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 파이썬을 찾을 수 없습니다. 설치 후 다시 시도하세요.
    pause
    exit /b
)

:: 2. Install PyInstaller
echo.
echo 📦 PyInstaller 설치 중...
pip install pyinstaller

:: 3. Build EXE
echo.
echo 🏗️ 실행 파일(EXE) 생성 중... (시간이 좀 걸립니다)
echo ----------------------------------------------------
:: Bundle core_v2 folder and config.json inside the EXE
pyinstaller --noconfirm --onefile --console ^
    --name "Moohyup_Generator" ^
    --add-data "core_v2;core_v2" ^
    --add-data "config.json;." ^
    --hidden-import "pydub" ^
    --hidden-import "PIL" ^
    --hidden-import "moviepy" ^
    launcher.py

echo.
if exist "dist\Moohyup_Generator.exe" (
    echo ✅ 생성 성공! 
    echo 📂 파일 위치: dist\Moohyup_Generator.exe
    echo.
    echo 👉 이제 'dist' 폴더 안에 있는 exe 파일만 있으면 어디서든 실행됩니다.
    echo    (단, SCRIPT_INPUT.txt 파일은 exe 옆에 있어야 합니다)
) else (
    echo ❌ 생성 실패. 오류 메시지를 확인하세요.
)

pause
