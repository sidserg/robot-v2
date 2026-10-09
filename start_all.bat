@echo off
cd /d "%~dp0"
echo Stopping...
python tools\stop_all.py
timeout /t 3 /nobreak >nul
echo Starting (silent)...
start "" /b pythonw tools\spawn_silent.py
start "" /b pythonw tools\dashboard.py
timeout /t 3 /nobreak >nul
echo Done.
echo   Dashboard: http://127.0.0.1:8770/
echo   Logs: logs/runner.out.log
