@echo off
title OpenLimiter Pro
cd /d "%~dp0"

echo ========================================================
echo             LAUNCHING OPENLIMITER PRO...
echo ========================================================

python main.py

if errorlevel 1 (
    echo.
    echo An error occurred while launching OpenLimiter Pro.
    pause
)
