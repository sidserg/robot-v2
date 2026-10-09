@echo off
cd /d C:\Users\cl\Desktop\RobotV2
taskkill /F /FI "WINDOWTITLE eq robotv2" >nul 2>nul
timeout /t 2 /nobreak >nul
start "robotv2" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python runner\multi.py"
