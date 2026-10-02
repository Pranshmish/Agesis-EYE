@echo off
cd /d "%~dp0"
echo ========================================================
echo   AGESIS EYE - LIVE ZERO-LAG BALLOON TRACKER (STAGE 04)
echo ========================================================
echo Model    : Model/agesis06.pt (Ultra-Low Latency, imgsz=384)
echo Resolution: 384x384
echo.
echo Controls:
echo   [q]  Quit
echo   [e]  Toggle EP-CLAHE Domain Transform (Enhance)
echo   [+]  Increase Confidence Threshold (+0.05)
echo   [-]  Decrease Confidence Threshold (-0.05)
echo   [s]  Save Debug Snapshot
echo.

set "PY_EXE=D:\Espressif\tools\python_env\idf5.3_py3.13_env\Scripts\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

"%PY_EXE%" "04 Laptop Inference\live_balloon_tracker.py" --model "Model\agesis06.pt" --conf 0.35 --imgsz 384
pause
