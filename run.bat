@echo off
cd /d "%~dp0"
py -3.12w vibecraft.py
if errorlevel 1 (
    echo.
    echo Fallback to regular Python launch...
    py -3.12 vibecraft.py
)
if errorlevel 1 pause
