@echo off
setlocal
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install dependencies. Install Python 3.11+ first.
  pause
  exit /b 1
)
echo Dependencies installed.
pause
