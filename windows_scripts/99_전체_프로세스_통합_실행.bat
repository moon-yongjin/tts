@echo off
chcp 65001 > nul
setlocal

:: [전체 프로세스 통합 마스터 스크립트 v3 - Windows Edition]
:: Cloud(Imagen) 전용 (Local 엔진 제외 버전)

cd /d "%~dp0"
set PYTHON_EXE=python
set DOWNLOADS_DIR=%USERPROFILE%\Downloads
set SCRIPT_FILE=대본.txt

echo ====================================================
echo 🚀 [MASTER FLOW v3] 무협 비디오 자동 제작 파이프라인
echo ====================================================

:: === 2. 모드 강제 설정 (Cloud) ===
echo.
echo ✅ [Cloud Mode] Google Imagen 및 API 엔진을 사용합니다.
echo.

set TOTAL_START=%TIME%

:: === 3. 입력 파일 검증 ===
if not exist "%SCRIPT_FILE%" (
    echo ❌ 오류: '%SCRIPT_FILE%' 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)
echo ✅ 입력 파일 확인 완료: %SCRIPT_FILE%

:: === 4. 공정 실행 ===

:: STEP 00: 사전 정리
echo.
echo 🧹 [STEP 00] 작업 공간 정리 중...
del /q "%DOWNLOADS_DIR%\*_part*.mp3" 2>nul
del /q "%DOWNLOADS_DIR%\*_part*.srt" 2>nul
del /q "%DOWNLOADS_DIR%\*_Full_Merged.mp3" 2>nul
del /q "%DOWNLOADS_DIR%\*_Full_Merged.srt" 2>nul
del /q "%DOWNLOADS_DIR%\*-*.mp3" 2>nul
del /q "%DOWNLOADS_DIR%\*_배경_효과음_레이어.mp3" 2>nul
echo ✅ 청소 완료.

:: STEP 01: 성우 음성 생성
echo.
echo 🎙️ [STEP 01] 성우 음성 및 자막 생성...
%PYTHON_EXE% core_v2\engine\muhyup_factory.py "%SCRIPT_FILE%"

:: STEP 01-1: 음성 자막 합치기
echo.
echo 🔗 [STEP 01-1] 음성/자막 병합...
%PYTHON_EXE% core_v2\01-1_file_merger.py

:: 파트 파일 정리
echo 🧹 [CLEANUP] 임시 파트 파일 삭제...
del /q "%DOWNLOADS_DIR%\*_part*.mp3" 2>nul
del /q "%DOWNLOADS_DIR%\*_part*.srt" 2>nul

:: STEP 02: 이미지 생성
echo.
echo 🎨 [STEP 02] 이미지 생성 파이프라인 가동...
call windows_scripts\02_이미지_생성_진행.bat

:: 검토 및 대기
echo.
echo ----------------------------------------------------
echo 👀 [검토 단계] 생성된 이미지를 확인하세요.
echo 📍 위치: Downloads\무협_... 폴더
echo ----------------------------------------------------
pause

:: STEP 03: 시네마틱 빈티지 영상 변환
echo.
echo 🎬 [STEP 03] 시네마틱 빈티지 영상 변환 (V3 View)...
%PYTHON_EXE% core_v2\03-1_cinematic_v3_vintage.py

:: STEP 04: BGM 오버레이
echo.
echo 🎵 [STEP 04] BGM 및 메인 음향 믹싱...
%PYTHON_EXE% core_v2\04_bgm_master.py

:: STEP 05: SFX 전용 레이어 생성
echo.
echo 🎹 [STEP 05] 추가 SFX 오디오 레이어 생성...
%PYTHON_EXE% core_v2\05_audio_layer_factory.py

:: STEP 07: 최종 마스터 통합 렌더링
echo.
echo 🏆 [STEP 07] 최종 마스터 렌더링 (다중 오디오 레이어 통합)...
%PYTHON_EXE% core_v2\07_master_integration.py

:: 마무리
echo.
echo ====================================================
echo ✨ [전체 공정 완료]
echo 📂 결과물 위치: Downloads 폴더 확인
echo ====================================================
echo.
pause
