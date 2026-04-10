@echo off
chcp 65001 > nul
title [TOOL] 무협 음성/자막 파일 합치기 (Step 01-1)

echo.
echo 🧩 [Step 01-1] 분할된 음성(MP3)과 자막(SRT) 합치기를 시작합니다...
echo ⏳ 다운로드 폴더에 있는 *_part1, *_part2 파일들을 자동으로 찾아서
echo ⏳ 하나의 'Full_Merged' 파일로 합쳐줍니다.
echo.

py -3.10 core_v2\01-1_file_merger.py

echo.
if errorlevel 1 (
    echo ❌ 병합 중 오류가 발생했습니다.
) else (
    echo ✅ 병합이 완료되었습니다! (Downloads 폴더를 확인하세요)
)

echo.
echo 작업을 완료하려면 아무 키나 누르세요...
pause > nul
