@echo off
:: Install pyinstaller if not already installed
pip install pyinstaller

:: Create a scheduled task to run the script at startup
schtasks /create /tn "UserActivityMonitor" /tr "%~dp0main.exe" /sc onlogon /rl highest

echo Scheduled task created. The program will now run at startup.

:: Convert Python script to executable
pyinstaller --onefile --noconsole main.py

echo Executable created as main.exe.