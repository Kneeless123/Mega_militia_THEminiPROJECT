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
    echo [*] Python not found. Installing Python 3.11...
    winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [!] Failed to install Python. Please install manually from python.org
        pause
        exit /b 1
    )
    echo [+] Python installed successfully
)

echo [*] Checking for virtual environment...
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created
) else (
    echo [+] Virtual environment already exists
)

echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [!] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [*] Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Failed to install requirements
    pause
    exit /b 1
)

echo.
echo ========================================
echo [+] Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run "launch.bat" to start the game
echo 2. Select "Host Game" or "Join Game"
echo 3. Enjoy!
echo.
pause