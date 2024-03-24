# BCDrecreate

## Overview
This batch script provides a menu-driven interface to perform various operations related to the Boot Configuration Data (BCD) on a Windows 10 system. It allows you to recreate BCD entries for Windows Boot Manager and Windows 10 Loader, as well as perform extensive recovery by executing additional commands such as `bcdboot` and `bootrec`.

## Usage
1. Boot your system into a recovery environment or Windows Preinstallation Environment (PE), download and run the script.
2. If your BCD is critically damaged and you cannot access the script, you can use the following one-liners by launching Command Prompt (CMD) and entering:
   - Recreate BCD entry for Windows Boot Manager:
     ```
     bcdedit /create {bootmgr} /d "Windows Boot Manager"
     ```
   - Recreate BCD entry for Windows 10 Loader:
     ```
     bcdedit /create /d "Windows 10" /application osloader
     ```
   - Extensive recovery using `bootrec`:
     ```
     bootrec /fixmbr && bootrec /fixboot && bootrec /rebuildbcd
     ```
   - Extensive recovery using `bcdboot`:
     ```
     bcdboot C:\Windows /s C: /f ALL
     ```

## Notes
- It is recommended to use this script in a recovery environment or Windows Preinstallation Environment (PE) to ensure system stability and avoid interference with running processes.
- Ensure that you run the script with administrative privileges to avoid permission issues.
- Use caution when performing extensive recovery as it may modify critical system configurations.
- If encountering errors or issues, refer to the script output for error messages or consult Windows documentation for troubleshooting steps.

