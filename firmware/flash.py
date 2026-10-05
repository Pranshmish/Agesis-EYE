"""
Agesis EYE - Direct ESP32 CLI Flasher
Flashes firmware/test directly without opening Arduino IDE GUI.
"""

import sys
import os
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKETCH_DIR = os.path.join(PROJECT_ROOT, "firmware", "test")
CLI_PATH = os.path.join(PROJECT_ROOT, "firmware", "tools", "arduino-cli.exe")
PORT = sys.argv[1] if len(sys.argv) > 1 else "COM14"

print("=" * 60)
print("  AGESIS EYE - DIRECT ESP32 FLASH TOOL")
print(f"  Target Port   : {PORT}")
print(f"  Sketch Folder : {SKETCH_DIR}")
print("=" * 60)

if not os.path.exists(CLI_PATH):
    print(f"\n[ERROR] arduino-cli.exe not found at: {CLI_PATH}")
    sys.exit(1)

# Step 1: Compile
print("\n[*] Compiling sketch...")
compile_cmd = [CLI_PATH, "compile", "--fqbn", "esp32:esp32:esp32", SKETCH_DIR]
res = subprocess.run(compile_cmd)
if res.returncode != 0:
    print("\n[ERROR] Compilation failed.")
    sys.exit(res.returncode)

print("\n" + "=" * 60)
print("  [ACTION REQUIRED ON ESP32 BOARD]")
print("  To ensure the ESP32 enters download mode:")
print("    1. Press and HOLD the [BOOT] button on your ESP32.")
print("    2. While holding BOOT, TAP the [EN / RST] button once.")
print("    3. Release the [BOOT] button.")
print("  The board is now 100% in Download Mode and ready to flash!")
print("=" * 60)
print("\n[*] Uploading firmware...")

upload_cmd = [
    CLI_PATH, "upload",
    "-p", PORT,
    "--fqbn", "esp32:esp32:esp32",
    "--upload-property", "upload.speed=921600",
    SKETCH_DIR
]
res = subprocess.run(upload_cmd)

if res.returncode != 0:
    print("\n[*] Retrying upload at 115200 baud...")
    upload_cmd[-2] = "upload.speed=115200"
    res = subprocess.run(upload_cmd)

if res.returncode == 0:
    print("\n" + "=" * 60)
    print("  [SUCCESS] Firmware flashed successfully directly to ESP32!")
    print("  Press the [EN / RST] button on your ESP32 to start running.")
    print("=" * 60)
else:
    print("\n[!] Flashing could not connect. If servos are plugged in, unplug their 5V/VIN wire, hold BOOT, and tap EN.")

sys.exit(res.returncode)
