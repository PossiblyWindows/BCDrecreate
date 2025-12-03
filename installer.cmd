@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ====== Path configuration ======
set DOWNLOADS=%USERPROFILE%\Downloads
set ICON_URL=https://www.uzdevumi.lv/favicon.ico
set ICON=%DOWNLOADS%\favicon.ico
set ZIP_URL=https://github.com/winpython/winpython/releases/download/17.2.20250920final/WinPython64-3.14.0.1dot.zip
set PYDIR=%DOWNLOADS%\WPy64-31401
set PYEXE=%PYDIR%\python\python.exe
set NOTEBOOKS=%PYDIR%\notebooks
set SCRIPT=%NOTEBOOKS%\main.py
set SCRIPT_URL=https://raw.githubusercontent.com/PossiblyWindows/BCDrecreate/refs/heads/main/main.py
set SHORTCUT="%USERPROFILE%\Desktop\Uzdevumi.lv Bot.lnk"

:: Suppress pip warnings
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_WARN_SCRIPT_LOCATION=1

:: ====== Start installer ======
echo [1/6] Lejupielādēju Ikonu...
curl -s -L -o "%ICON%" "%ICON_URL%"

echo [2/6] Izdzēšu veco WinPython instalāciju...
if exist "%PYDIR%" rd /s /q "%PYDIR%"

echo [3/6] Ieinstelēju WinPython...
curl -s -L -o "%DOWNLOADS%\winpy.zip" "%ZIP_URL%"
tar -xf "%DOWNLOADS%\winpy.zip" -C "%DOWNLOADS%"

if not exist "%PYEXE%" (
    echo Kļūda: Neizdevās izvilkt ZIP failu.
    pause
    exit /b
)

echo [4/6] Lūdzu uzgaidiet (1-5 min)...
"%PYEXE%" -m pip install -q --upgrade pip >nul 2>&1
"%PYEXE%" -m pip install -q requests openai selenium undetected-chromedriver customtkinter >nul 2>&1

echo [5/6] Lejupielādēju botu...
curl -s -L -o "%SCRIPT%" "%SCRIPT_URL%"

echo [6/6] Izveidoju saīsni...

:: ====== Create shortcut with PowerShell ======
powershell -NoLogo -NoProfile -Command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
    "$s.TargetPath='%PYEXE%';" ^
    "$s.Arguments='\"%SCRIPT%\"';" ^
    "$s.WorkingDirectory='%NOTEBOOKS%';" ^
    "$s.IconLocation='%ICON%';" ^
    "$s.Save()"

echo Gatavs! Saīsne izveidota uz darbvirsmas.
pause
