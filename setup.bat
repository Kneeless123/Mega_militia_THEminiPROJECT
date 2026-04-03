@echo off

winget install Python.Python.3.11

py -3.11.9 -m venv venv

call venv\Scripts\activate
pip install -r requirements.txt

echo Setup complete. Run launch.bat to start the game.
pause