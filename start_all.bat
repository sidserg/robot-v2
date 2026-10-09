@echo off
cd /d C:\Users\cl\Desktop\RobotV2
start "robotv2" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python runner\multi.py"
timeout /t 3 /nobreak >nul
start "watch_robot" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python tools\watch_robot.py"
start "pilot" cmd /k "cd /d C:\Users\cl\Desktop\RobotV2 && python tools\pilot.py"
