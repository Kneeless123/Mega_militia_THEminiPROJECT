@echo off
REM Join a specific server by IP address
REM Usage: join_server.bat <server_ip>
REM Example: join_server.bat 192.168.1.100

if "%1"=="" (
    echo Usage: join_server.bat ^<server_ip^>
    echo Example: join_server.bat 192.168.1.100
    echo.
    echo This script will set the MEGA_SERVER_IP environment variable
    echo and launch the game to connect to that server.
    pause
    exit /b 1
)

echo [*] Setting MEGA_SERVER_IP=%1
set MEGA_SERVER_IP=%1

echo [*] Launching game...
python game.py
pause
