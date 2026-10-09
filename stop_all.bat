@echo off
cd /d "%~dp0"
python tools\\stop_all.py
echo.
timeout /t 3 /nobreak >nul
