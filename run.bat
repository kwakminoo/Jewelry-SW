@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment was not found.
    echo Run setup_app.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m jewelry.main
set "JEWELRY_EXIT=%ERRORLEVEL%"

if not "%JEWELRY_EXIT%"=="0" (
    echo.
    echo [ERROR] Jewelry SW failed to start. Exit code: %JEWELRY_EXIT%
    pause
)

exit /b %JEWELRY_EXIT%
