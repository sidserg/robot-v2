@echo off
cd /d "%~dp0"
echo Stopping...
python tools\\stop_all.py
timeout /t 3 /nobreak >nul
echo Starting (silent)...
start "" /b pythonw tools\\spawn_silent.py
timeout /t 3 /nobreak >nul
echo Done. Check logs/runner.out.log
