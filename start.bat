@echo off
title FraudGuard AI - Launching...

echo ============================================
echo  FraudGuard AI - Setup and Launch
echo  Deborah Patrick's ML Fraud Detection System
echo ============================================
echo.

:: Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed.
    echo Please download and install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [..] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo [..] Installing dependencies (first run may take a few minutes)...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Set default credentials
set FRAUDGUARD_ADMIN_PW=admin123
set FRAUDGUARD_ANALYST_PW=analyst123

:: Launch the application
echo.
echo ============================================
echo  Starting FraudGuard AI...
echo  Open http://127.0.0.1:5000 in your browser
echo  Admin: admin / admin123
echo  Analyst: analyst / analyst123
echo ============================================
echo.

start http://127.0.0.1:5000
python app.py

pause
