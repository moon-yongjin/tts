@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [TOOL] 무협 종합 V4 통합 엔진 (영상+자막+음성+SFX+앰비언스)

echo.
echo 🚀 [Mu-hyup Master V4 Full] 종합 통합 렌더링을 시작합니다...
echo ⏳ 영상 병합 + 자막 + 성우 음성 + 효과음(SFX) + 환경음(Ambi)
echo ⏳ 복합 오디오 믹싱 과정이 포함되어 시간이 다소 소요될 수 있습니다.
echo.

py -3.10 muhyup_master_v4_all_audio.py

if errorlevel 1 (
    echo.
    echo ❌ 렌더링 중 오류가 발생했습니다.
) else (
    echo.
    echo ✅ 모든 작업이 성공적으로 완료되었습니다! (V4 통합본 생성됨)
)

echo.
echo 작업을 완료하려면 아무 키나 누르세요...
pause > nul
