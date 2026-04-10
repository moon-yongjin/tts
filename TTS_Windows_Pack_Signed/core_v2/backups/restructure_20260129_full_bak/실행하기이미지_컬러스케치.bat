@echo off
title AI 이미지 디렉터 [컬러스케치]
cd /d "%~dp0"
chcp 65001 > nul
py -3.10 visual_director.py 컬러스케치
pause
