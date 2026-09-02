@echo off
setlocal
cd /d "%~dp0"

set "JEWELRY_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%JEWELRY_PYTHON%" (
    echo [ERROR] Python 3.12 was not found at:
    echo %JEWELRY_PYTHON%
    pause
    exit /b 1
)

"%JEWELRY_PYTHON%" -m venv --clear .venv
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo.
echo Setup completed. Run run_app.bat.
pause
exit /b 0

:failed
echo.
echo [ERROR] Setup failed.
pause
exit /b 1
