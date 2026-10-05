@echo off
setlocal
echo ========================================================
echo   AGESIS EYE - ESP32-CAM TACTICAL ONE-CLICK FLASHER
echo ========================================================

set PORT=COM15
if not "%~1"=="" set PORT=%~1

set TOOLS_DIR=%~dp0tools
set CLI=%TOOLS_DIR%\arduino-cli.exe
set SKETCH_DIR=%~dp0esp32_cam_stream

if not exist "%CLI%" (
    echo [ERROR] arduino-cli.exe not found in %TOOLS_DIR%!
    exit /b 1
)

echo.
echo [*] Compiling ESP32-CAM firmware: %SKETCH_DIR%...
"%CLI%" compile --fqbn esp32:esp32:esp32cam "%SKETCH_DIR%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compilation failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo   READY TO FLASH ESP32-CAM ON %PORT%
echo   IMPORTANT FOR ESP32-CAM:
echo   1. Ensure IO0 is connected to GND (or hold BOOT)
echo   2. Press the RST button on the ESP32-CAM board
echo   3. When upload finishes: REMOVE IO0 from GND and press RST!
echo ========================================================
echo.

"%CLI%" upload -p %PORT% --fqbn esp32:esp32:esp32cam --upload-property upload.speed=460800 "%SKETCH_DIR%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] ESP32-CAM Flash complete on %PORT%!
    echo   Disconnect IO0 from GND, then press RST on the board.
    echo ========================================================
) else (
    echo.
    echo [*] Retrying at 115200 baud... (Hold IO0 to GND and press RST)
    "%CLI%" upload -p %PORT% --fqbn esp32:esp32:esp32cam --upload-property upload.speed=115200 "%SKETCH_DIR%"
)
