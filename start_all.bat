@echo off
cd /d "%~dp0"
echo Stopping...
python tools\stop_all.py
timeout /t 3 /nobreak >nul
echo Starting...
start "robotv2" cmd /k python runner\multi.py
echo Done. Dashboard: http://127.0.0.1:8770/
