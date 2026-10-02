@echo off
cd /d "%~dp0"
echo ========================================================
echo   AGESIS EYE - LIVE ONNX BALLOON TRACKER (STAGE 04)
echo ========================================================
echo Model     : models/agesis06.onnx (Ultra-Fast ONNX Runtime)
echo Resolution: 384x384
echo.
echo Controls:
echo   [q]  Quit / Exit
echo   [e]  Toggle EP-CLAHE Domain Transform (Enhance)
echo   [+]  Increase Confidence Threshold (+0.05)
echo   [-]  Decrease Confidence Threshold (-0.05)
echo   [s]  Save Debug Snapshot
echo.

set "PY_EXE=D:\Espressif\tools\python_env\idf5.3_py3.13_env\Scripts\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

"%PY_EXE%" "live_balloon_tracker.py" --model "models\agesis06.onnx" --conf 0.35 --imgsz 384
pause
