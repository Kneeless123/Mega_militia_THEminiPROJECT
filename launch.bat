@echo off
setlocal enabledelayedexpansion

REM Check if virtual environment exists
if not exist "venv" (
    echo [!] Virtual environment not found
    echo [*] Running setup.bat first...
    call setup.bat
    if %errorlevel% neq 0 (
        echo [!] Setup failed
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call pygame\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [!] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Run the game
echo [*] Launching MEGA MILITIA...
python game.py
if %errorlevel% neq 0 (
    echo [!] Game crashed. Check the error above.
    pause
)

exit /b 0