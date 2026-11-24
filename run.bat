@echo off
title OpenLimiter Pro
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.10 or newer, then run:
    echo     python -m pip install -r requirements.txt
    pause
    exit /b 1
)

python -c "import PySide6, psutil" >nul 2>nul
if errorlevel 1 (
    echo OpenLimiter dependencies are missing. From this folder run:
    echo     python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ========================================================
echo             LAUNCHING OPENLIMITER PRO...
echo ========================================================

python main.py

if errorlevel 1 (
    echo.
    echo An error occurred while launching OpenLimiter Pro.
    pause
)
