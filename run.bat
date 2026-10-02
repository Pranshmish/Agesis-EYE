@echo off
cd /d "%~dp0"
title Agesis EYE - Ground Station
cls
echo ========================================================
echo   AGESIS EYE - AUTONOMOUS TARGETING GROUND STATION
echo ========================================================
echo.
echo   [1] Initializing AI Tracking Engine (agesis06.onnx)...
echo   [2] Starting Fast Web Ground Station on http://127.0.0.1:8000...
echo   [3] Opening Tactical HUD in your web browser...
echo.
echo   Press Ctrl+C in this window anytime to stop the server.
echo ========================================================
echo.

set "PY_EXE=D:\Espressif\tools\python_env\idf5.3_py3.13_env\Scripts\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

:: Launch browser in background after 1.5 seconds
start /b cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8000"

:: Start Backend FastAPI Server
"%PY_EXE%" "backend\app.py"
pause
