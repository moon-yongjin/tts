@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [TOOL] 무협 종합 통합 엔진 (영상+자막+음성)

echo.
echo 🚀 [Mu-hyup Master Full] 종합 통합 렌더링을 시작합니다...
echo ⏳ 영상 병합, 자막 삽입, 음원 합성을 동시에 진행합니다.
echo ⏳ 인코딩 과정이 포함되어 있어 수 분 정도 소요될 수 있습니다.
echo.

py -3.10 core_v2\07_master_integration.py

if errorlevel 1 (
    echo.
    echo ❌ 렌더링 중 오류가 발생했습니다.
) else (
    echo.
    echo ✅ 모든 작업이 성공적으로 완료되었습니다!
)

echo.
echo 작업을 완료하려면 아무 키나 누르세요...
pause > nul
