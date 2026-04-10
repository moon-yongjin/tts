@echo off
title AI 이미지 디렉터 [수묵화]
cd /d "%~dp0"
chcp 65001 > nul
py -3.10 visual_director.py 수묵화
pause
