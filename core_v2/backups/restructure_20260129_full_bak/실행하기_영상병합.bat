@echo off
chcp 65001 > nul
mode con: cols=120 lines=50
title [TOOL] 영상 초고속 병합 (No Re-encoding)

echo.
echo 📂 현재 폴더의 모든 .mp4 파일을 하나로 합칩니다.
echo ⏳ 파일 목록 생성 및 정렬 중...

:: PowerShell을 사용하여 자연스러운 숫자 정렬(Natural Sort) 후 리스트 생성
:: 1, 2, 10 순서가 1, 10, 2로 섞이지 않도록 처리
powershell -Command "Get-ChildItem -Filter *.mp4 | Where-Object { $_.Name -ne 'output.mp4' } | Sort-Object { [regex]::Replace($_.Name, '\d+', { $args[0].Value.PadLeft(10, '0') }) } | ForEach-Object { 'file ''{0}''' -f $_.Name } | Out-File -Encoding utf8 mylist.txt"

if not exist mylist.txt (
    echo ❌ 병합할 MP4 파일이 없습니다.
    pause
    goto :EOF
)

echo.
echo 📋 병합 대상 목록:
type mylist.txt
echo.

echo 🚀 병합 시작 (output.mp4)...
ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4 -y

echo.
if exist output.mp4 (
    echo ✅ 병합 완료! (output.mp4)
    del mylist.txt
) else (
    echo ❌ 병합 실패.
)

pause
