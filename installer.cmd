@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ====== Konfigurācija ======
set DOWNLOADS=%USERPROFILE%\Downloads
set ICON_URL=https://www.uzdevumi.lv/favicon.ico
set ICON=%DOWNLOADS%\favicon.ico
set DEFAULT_ZIP_URL=https://github.com/winpython/winpython/releases/download/17.2.20250920final/WinPython64-3.14.0.1dot.zip
set DEFAULT_PYDIR=%DOWNLOADS%\WPy64-31401
set DEFAULT_PYEXE=%DEFAULT_PYDIR%\python\python.exe
set NOTEBOOKS=%DEFAULT_PYDIR%\notebooks
set SCRIPT=%NOTEBOOKS%\main.py
set SCRIPT_URL=https://raw.githubusercontent.com/PossiblyWindows/BCDrecreate/refs/heads/main/main.py
set SHORTCUT=%USERPROFILE%\Desktop\Uzdevumi.lv Bot.lnk

:: Suppress pip warnings
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_WARN_SCRIPT_LOCATION=1

:: ===================================================================
::   WINPYTHON DETECTION (SEARCHES COMMON PATHS + ALL DRIVES A–Z)
:: ===================================================================

echo Meklēju esošas WinPython instalācijas...
set FOUND=0
set FOUND_FIRST=

:: Check common directories patterns
for /d %%A in ("%USERPROFILE%\WPy*" "%USERPROFILE%\Desktop\WPy*" "%DOWNLOADS%\WPy*" "%PROGRAMFILES%\WPy*" "%PROGRAMFILES(X86)%\WPy*" "C:\WPy*") do (
    if exist "%%~A" (
        set FOUND=1
        if "!FOUND_FIRST!"=="" set "FOUND_FIRST=%%~A"
        echo Atrasts: %%~A
    )
)

:: Check all drives A–Z for folders like WPy*
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    for /d %%B in ("%%D:\\WPy*") do (
        if exist "%%~B" (
            set FOUND=1
            if "!FOUND_FIRST!"=="" set "FOUND_FIRST=%%~B"
            echo Atrasts: %%~B
        )
    )
)

if %FOUND%==1 (
    echo.
    echo Konstatēta esoša WinPython instalācija. Lūdzu izvēlieties: dzēst visu instalāciju vai turpināt tikai skripta instalēšanu.
    echo.
    echo 1) Dzēst visus atrastos WinPython direktorijus un turpināt instalēšanu (iestalēt WinPython no ZIP).
    echo 2) Tikai instalēt skriptu esošā WinPython instalācijā (nelejupielādēt WinPython).
    echo 3) Atcelt un iziet.
    echo.
    set /p USERCHOICE=Jūsu izvēle (1/2/3): 
    if "%USERCHOICE%"=="3" (
        echo Darbība anulēta.
        pause
        goto :EOF
    )
    if "%USERCHOICE%"=="1" (
        echo Dzēšu atrastās WinPython direktorijas...
        :: Dzēst visas atrastās mapes (common locations)
        for /d %%A in ("%USERPROFILE%\WPy*" "%USERPROFILE%\Desktop\WPy*" "%DOWNLOADS%\WPy*" "%PROGRAMFILES%\WPy*" "%PROGRAMFILES(X86)%\WPy*" "C:\WPy*") do (
            if exist "%%~A" (
                echo Dzēšu: %%~A
                rd /s /q "%%~A" 2>nul
            )
        )
        :: Dzēst visas atrastās mapes uz visiem diskiem
        for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
            for /d %%B in ("%%D:\\WPy*") do (
                if exist "%%~B" (
                    echo Dzēšu: %%~B
                    rd /s /q "%%~B" 2>nul
                )
            )
        )
        echo Dzēšana pabeigta.
        set "DO_FULL_INSTALL=1"
    ) else if "%USERCHOICE%"=="2" (
        echo Instalēšu tikai skriptu esošajā WinPython instalācijā.
        set "DO_FULL_INSTALL=0"
        :: ja nav definēta FIRST found path, izmanto default
        if defined FOUND_FIRST (
            set "PYDIR=!FOUND_FIRST!"
        ) else (
            set "PYDIR=%DEFAULT_PYDIR%"
        )
        set "PYEXE=!PYDIR!\python\python.exe"
        set "NOTEBOOKS=!PYDIR!\notebooks"
        set "SCRIPT=!NOTEBOOKS!\main.py"
    ) else (
        echo Nezināma izvēle. Iziet.
        pause
        goto :EOF
    )
) else (
    :: nav atrasts - veicam pilno instalāciju
    set "DO_FULL_INSTALL=1"
)

:: ===================================================================
::   START INSTALL (veic tikai, ja DO_FULL_INSTALL==1)
:: ===================================================================

if "%DO_FULL_INSTALL%"=="1" (
    echo [1/7] Lejupielādēju ikonu...
    curl -s -L -o "%ICON%" "%ICON_URL%"

    echo [2/7] Izdzēšu (ja nepieciešams) iepriekšējo WinPython direktoriju...
    if exist "%DEFAULT_PYDIR%" rd /s /q "%DEFAULT_PYDIR%"

    echo [3/7] Lejupielādēju WinPython ZIP...
    curl -s -L -o "%DOWNLOADS%\winpy.zip" "%DEFAULT_ZIP_URL%"

    echo [4/7] Izpakoju WinPython...
    tar -xf "%DOWNLOADS%\winpy.zip" -C "%DOWNLOADS%"

    :: mēģinām noteikt PYEXE pēc noklusējuma vai pēc izvilktās mapes
    if exist "%DEFAULT_PYEXE%" (
        set "PYEXE=%DEFAULT_PYEXE%"
        set "PYDIR=%DEFAULT_PYDIR%"
        set "NOTEBOOKS=%PYDIR%\notebooks"
        set "SCRIPT=%NOTEBOOKS%\main.py"
    ) else (
        :: mēģinām atrast WPy mapu, kas tikko tika izvilkta
        for /d %%Z in ("%DOWNLOADS%\WPy*") do (
            if exist "%%~Z\python\python.exe" (
                set "PYDIR=%%~Z"
                set "PYEXE=%%~Z\python\python.exe"
                set "NOTEBOOKS=%%~Z\notebooks"
                set "SCRIPT=!NOTEBOOKS!\main.py"
                goto :after_detect
            )
        )
        :after_detect
    )

    if not exist "%PYEXE%" (
        echo Kļūda: Neizdevās atrast python izpildāmo pēc izpakošanas.
        pause
        exit /b
    )

    echo [5/7] Instalēju Python pakotnes (pip) — lūdzu uzgaidiet...
    "%PYEXE%" -m pip install -q --upgrade pip >nul 2>&1
    "%PYEXE%" -m pip install -q requests openai selenium undetected-chromedriver customtkinter >nul 2>&1
) else (
    echo [INFO] Izvēlēts tikai skripta instalēšanas režīms. Nepārinstalēšu WinPython.
    if not exist "!PYEXE!" (
        echo Brīdinājums: norādītais Python izpildāmais var nebūt pieejams: !PYEXE!
    )
)

:: ===================================================================
::   SKRIPTA LEJUPIELĀDE
:: ===================================================================

echo [6/7] Lejupielādēju botu (skriptu)...
if not exist "%NOTEBOOKS%" mkdir "%NOTEBOOKS%" 2>nul
curl -s -L -o "%SCRIPT%" "%SCRIPT_URL%"

if not exist "%SCRIPT%" (
    echo Kļūda: Neizdevās lejupielādēt skriptu uz %SCRIPT%.
    pause
    exit /b
)

:: ===================================================================
::   SAĪSNES IZVEIDE UN PIELĀGOŠANA (PowerShell)
:: ===================================================================

echo [7/7] Izveidoju saīsni un veicu tās pielāgošanu...

:: PowerShell komanda ar papildu lauku iestatījumiem: Description, HotKey, WindowStyle
powershell -NoLogo -NoProfile -Command ^
    "$s = (New-Object -COM WScript.Shell).CreateShortcut('!SHORTCUT!');" ^
    "$s.TargetPath = '!PYEXE!';" ^
    "$s.Arguments = '\"!SCRIPT!\"';" ^
    "$s.WorkingDirectory = '!NOTEBOOKS!';" ^
    "$s.IconLocation = '!ICON!';" ^
    "$s.Description = 'Uzdevumi.lv Bot — automatizēts rīks';" ^
    "$s.Hotkey = 'Ctrl+Alt+U';" ^
    "$s.WindowStyle = 1;" ^
    "$s.Save();"

echo Gatavs! Saīsne izveidota uz darbvirsmas: %SHORTCUT%
pause
