@echo off
pushd "%~dp0"
cd ..
"C:\Users\moori\AppData\Local\Programs\Python\Python310\python.exe" engine\muhyup_factory.py scripts\test_voices.txt
pause
popd
