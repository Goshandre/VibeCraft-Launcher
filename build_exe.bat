@echo off
py -3 -m pip install -r requirements.txt
py -3 -m PyInstaller --noconfirm --clean --windowed --name VibeCraftLauncher --icon vibecraft_icon.ico vibecraft.py
echo.
echo EXE (if build succeeded): dist\VibeCraftLauncher.exe
pause
