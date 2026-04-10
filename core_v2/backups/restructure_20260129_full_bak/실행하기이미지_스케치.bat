@echo off
title AI 이미지 디렉터 [스케치]
cd /d "%~dp0"
chcp 65001 > nul
py -3.10 visual_director.py 스케치
pause
