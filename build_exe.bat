@echo off
title FraudGuard AI - Build Standalone Executable

echo ============================================
echo  FraudGuard AI - Build Executable
echo  Deborah Patrick's ML Fraud Detection System
echo ============================================
echo.

:: Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed.
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check PyInstaller
pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [..] Installing PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: Install project dependencies
echo [..] Installing project dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Clean previous build
if exist "dist\FraudGuardAI" rmdir /s /q "dist\FraudGuardAI"
if exist "build" rmdir /s /q "build"
if exist "FraudGuardAI.spec" del "FraudGuardAI.spec"

:: Build executable
echo [..] Building standalone executable (this may take several minutes)...
pyinstaller --onefile --windowed --name "FraudGuardAI" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "requirements.txt;." ^
    --add-data "start.bat;." ^
    --hidden-import sklearn ^
    --hidden-import sklearn.ensemble ^
    --hidden-import sklearn.preprocessing ^
    --hidden-import sklearn.model_selection ^
    --hidden-import sklearn.metrics ^
    --hidden-import xgboost ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import sqlite3 ^
    --hidden-import flask ^
    app.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

:: Copy additional files
if exist "dist\FraudGuardAI" (
    xcopy /E /I /Y "templates" "dist\FraudGuardAI\templates" >nul
    xcopy /E /I /Y "static" "dist\FraudGuardAI\static" >nul
    copy "start.bat" "dist\FraudGuardAI\" >nul
    copy "requirements.txt" "dist\FraudGuardAI\" >nul
    copy "landing.html" "dist\FraudGuardAI\" >nul
)

echo.
echo ============================================
echo  Build Complete!
echo.
echo  Standalone executable created at:
echo  dist\FraudGuardAI\FraudGuardAI.exe
echo.
echo  Users can run it directly without
echo  installing Python or any libraries.
echo ============================================
echo.

pause
