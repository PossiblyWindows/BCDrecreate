@echo off
setlocal enabledelayedexpansion

:menu
cls
echo Menu:
echo 1. Recreate BCD entry for Windows Boot Manager
echo 2. Recreate BCD entry for Windows 10 Loader
echo 3. Extensive Recovery (perform extensive fixes)
echo 4. Exit

set /p choice=Enter your choice: 

if "%choice%"=="1" (
    call :RecreateBootManagerEntry
) else if "%choice%"=="2" (
    call :RecreateWindows10Entry
) else if "%choice%"=="3" (
    call :ExtensiveRecovery
) else if "%choice%"=="4" (
    exit /b
) else (
    echo Invalid choice. Please enter a valid option.
    timeout /t 3 >nul
    goto :menu
)

:RecreateBootManagerEntry
echo Recreating BCD entry for Windows Boot Manager...
bcdedit /create {bootmgr} /d "Windows Boot Manager"
call :CheckError
echo BCD entry for Windows Boot Manager has been recreated successfully.
timeout /t 3 >nul
goto :menu

:RecreateWindows10Entry
echo Recreating BCD entry for Windows 10 Loader...
bcdedit /create /d "Windows 10" /application osloader
call :CheckError
echo BCD entry for Windows 10 Loader has been recreated successfully.
timeout /t 3 >nul
goto :menu

:ExtensiveRecovery
echo Performing extensive recovery...
echo Recreating BCD entry for Windows Boot Manager...
bcdedit /create {bootmgr} /d "Windows Boot Manager"
call :CheckError
echo Recreating BCD entry for Windows 10 Loader...
bcdedit /create /d "Windows 10" /application osloader
call :CheckError
echo Running bcdboot...
bcdboot C:\Windows /s C: /f ALL
call :CheckError
echo Running bootrec...
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd
call :CheckError
echo Extensive recovery completed successfully.
timeout /t 5 >nul
goto :menu

:CheckError
if %errorlevel% neq 0 (
    echo An error occurred. Exiting...
    exit /b %errorlevel%
)

:end
endlocal
