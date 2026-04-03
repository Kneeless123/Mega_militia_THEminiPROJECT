@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   MEGA MILITIA - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo [*] Checking for virtual environment...
if not exist "pygame" (
    echo [*] Creating virtual environment 'pygame'...
    python -m venv pygame
    if %errorlevel% neq 0 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created
) else (
    echo [+] Virtual environment 'pygame' already exists
)

echo [*] Activating virtual environment...
call pygame/Scripts/activate
if %errorlevel% neq 0 (
    echo [!] Activation failed, but proceeding with direct paths...
)

echo [*] Installing dependencies...
pygame\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
pygame\Scripts\python.exe -m pip install pygame pillow
if %errorlevel% neq 0 (
    echo [!] Failed to install dependencies.
    exit /b 1
)

echo.
echo ========================================
echo [+] Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run "launch.bat" to start the game
echo 2. The game will automatically join a host or start hosting
echo.