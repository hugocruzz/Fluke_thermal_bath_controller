@echo off
echo ========================================
echo   Thermal Bath Controller Launcher
echo ========================================

rem Find the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Check if Python 3 is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3 to run this application.
    pause
    exit /b 1
)

rem Create virtual environment if it doesn't exist
if not exist venv\ (
    echo Setting up virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Please ensure venv module is available.
        pause
        exit /b 1
    )
)

rem Activate virtual environment
call venv\Scripts\activate.bat

rem Install requirements
echo Installing required packages...
pip install -r requirements.txt

rem Launch the application
echo Launching Thermal Bath Controller...
python gui_pi.py

rem Deactivate virtual environment when done
call venv\Scripts\deactivate.bat