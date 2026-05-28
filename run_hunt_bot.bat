@echo off
title Stock Hunt Telegram Bot
set PYTHONUTF8=1

echo Dang kich hoat moi truong ao .venv...
call "%USERPROFILE%\.venv\Scripts\activate.bat"

echo Dang chuyen vao thu muc project root...
cd /d "%~dp0.."

echo Dang khoi chay Stock Hunt Bot...
python -m stock_hunt.main %*

pause

