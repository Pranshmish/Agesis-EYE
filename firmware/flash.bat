@echo off
setlocal
echo ========================================================
echo   AGESIS EYE - DIRECT ESP32 FLASH TOOL (NO ARDUINO IDE)
echo ========================================================

set PORT=COM14
if not "%~1"=="" set PORT=%~1

set TOOLS_DIR=%~dp0tools
set CLI=%TOOLS_DIR%\arduino-cli.exe
set SKETCH_DIR=%~dp0test

if not exist "%CLI%" (
    echo [ERROR] arduino-cli.exe not found in %TOOLS_DIR%!
    exit /b 1
)

echo.
echo [*] Compiling sketch: %SKETCH_DIR%...
"%CLI%" compile --fqbn esp32:esp32:esp32 "%SKETCH_DIR%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compilation failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo   READY TO FLASH ON %PORT%
echo   IMPORTANT: When "Connecting..." appears below:
echo   PRESS AND HOLD the [BOOT] button on the ESP32 board
echo   until you see "Writing at 0x00010000..." or a percentage!
echo   (Tip: If servos are plugged in, temporarily disconnect
echo    their 5V/VIN wire so the USB reset circuit can trigger)
echo ========================================================
echo.

"%CLI%" upload -p %PORT% --fqbn esp32:esp32:esp32 --upload-property upload.speed=460800 "%SKETCH_DIR%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Direct flash complete on %PORT%!
    echo ========================================================
) else (
    echo.
    echo [*] Retrying at 115200 baud... Remember to HOLD THE BOOT BUTTON!
    "%CLI%" upload -p %PORT% --fqbn esp32:esp32:esp32 --upload-property upload.speed=115200 "%SKETCH_DIR%"
)
