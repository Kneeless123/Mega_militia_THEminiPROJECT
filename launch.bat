@echo off
setlocal enabledelayedexpansion

REM Check if 'pygame' virtual environment exists
if not exist "pygame" (
    echo [!] Virtual environment 'pygame' not found.
    echo [*] Running setup.bat first...
    call setup.bat
    if %errorlevel% neq 0 (
        echo [!] Setup failed.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call pygame/Scripts/activate
if %errorlevel% neq 0 (
    echo [!] Failed to activate virtual environment.
)

echo [*] Launching MEGA MILITIA...
python game.py
if %errorlevel% neq 0 (
    echo [!] Game closed with an error.
)

exit /b 0