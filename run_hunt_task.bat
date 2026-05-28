@echo off
:: Script danh rieng cho Task Scheduler (khong co lenh pause de tranh treo tien trinh)
set PYTHONUTF8=1

:: Chuyen vao thu muc goc cua project
cd /d "%~dp0.."

:: Kich hoat moi truong ao
call "%USERPROFILE%\.venv\Scripts\activate.bat"

:: Chay bot voi tham so --now de quet 1 lan roi tu dong thoat
python -m stock_hunt.main --now
