@echo off
cd /d "%~dp0"
py -3.12 vibecraft.py
if errorlevel 1 pause
