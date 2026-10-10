@echo off

cd /d C:\Users\cl\Desktop\RobotV2

taskkill /F /IM python.exe >nul 2>nul

timeout /t 2 /nobreak >nul

start "robotv2" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python runner\multi.py"



timeout /t 4 /nobreak >nul

start "chart" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python tools\chart.py"

timeout /t 6 /nobreak >nul
start "watchdog" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python tools\watch_robot.py"
