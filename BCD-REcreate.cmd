@echo off
setlocal enabledelayedexpansion

REM Function to check if the command was successful
:CheckError
if %errorlevel% neq 0 (
    echo Error: %1
    echo Exiting...
    exit /b %errorlevel%
)

REM Function to backup the BCD
:BackupBCD
echo Backing up Boot Configuration Data (BCD)...
bcdedit /export C:\BCD_Backup
call :CheckError "Failed to backup BCD"

REM Function to repair the BCD
:RepairBCD
echo Repairing Boot Configuration Data (BCD)...
bcdedit /import C:\BCD_Backup
call :CheckError "Failed to repair BCD"

REM Function to restore boot files
:RestoreBootFiles
echo Restoring boot files...
bcdboot C:\Windows /s C:
call :CheckError "Failed to restore boot files"

REM Function to reverse effects of BCDEDIT /delete {current}
:ReverseDelete
echo Reversing effects of BCDEDIT /delete {current}...
bcdedit /create {bootmgr} /d "Windows Boot Manager"
bcdedit /create /d "Windows" /application osloader
for /f "tokens=2 delims={}" %%i in ('bcdedit.exe /create /d "Windows" /application osloader') do set guid={%%i}
bcdedit /set %guid% device partition=C:
bcdedit /set %guid% path \Windows\system32\winload.exe
bcdedit /set %guid% systemroot \Windows
bcdedit /displayorder %guid% /addlast
call :CheckError "Failed to reverse delete operation"

:Menu
cls
echo Select an option:
echo 1. Backup BCD
echo 2. Repair BCD
echo 3. Restore boot files
echo 4. Reverse effects of BCDEDIT /delete {current}
echo 5. All-in-One
echo 6. Exit

set /p choice="Enter your choice: "

if "%choice%"=="1" (
    call :BackupBCD
    goto Menu
) else if "%choice%"=="2" (
    call :RepairBCD
    goto Menu
) else if "%choice%"=="3" (
    call :RestoreBootFiles
    goto Menu
) else if "%choice%"=="4" (
    call :ReverseDelete
    goto Menu
) else if "%choice%"=="5" (
    call :BackupBCD
    call :RepairBCD
    call :RestoreBootFiles
    call :ReverseDelete
    echo All operations completed successfully.
    timeout /t 2 >nul
    goto Menu
) else if "%choice%"=="6" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    timeout /t 2 >nul
    goto Menu
)

:end
endlocal
