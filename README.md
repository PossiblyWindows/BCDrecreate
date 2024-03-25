# Windows Boot Repair Script

This batch script is designed to repair Windows boot configuration and restore bootability using `bcdedit` and `bcdboot`.

## Features

- **Backup BCD**: Creates a backup of the Boot Configuration Data (BCD) before making any changes.
- **Repair BCD**: Repairs the Boot Configuration Data (BCD) to fix boot-related issues.
- **Restore Boot Files**: Restores boot files to ensure Windows boots properly.
- **Reverse Delete Operation**: Reverses the effects of `BCDEDIT /delete {current}` by restoring the deleted boot entry.
- **Menu**: Provides a menu interface for easy selection of individual operations or an "All-in-One" option to perform all operations sequentially.

## Usage

1. Clone or download the script.
2. Run the script with administrative privileges (right-click > Run as administrator).
3. Select an option from the menu to perform the desired operation.
4. Follow the on-screen instructions if any errors occur.

## Disclaimer

- Use this script at your own risk. Modifying boot configuration data can have serious consequences if not done correctly.
- Always ensure you have backups of important data before making changes to the boot configuration.
- The script is provided as-is without any warranties.

## License

This project is licensed under the [MIT License](LICENSE).
