import subprocess
import serial.tools.list_ports
import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_EXE = os.path.join(BASE_DIR, "tools", "arduino-cli.exe")
SKETCH_DIR = os.path.join(BASE_DIR, "esp32_cam_stream")

def find_esp_port():
    ports = list(serial.tools.list_ports.comports())
    non_bt = [p for p in ports if "bluetooth" not in p.description.lower()]
    if non_bt:
        return non_bt[0].device
    return None

def main():
    print("=" * 60)
    print("  ESP32-CAM One-Click Direct Flasher (Zero Arduino IDE)")
    print("=" * 60)
    
    port = find_esp_port()
    if not port:
        print("[!] ESP32 USB port not currently detected.")
        print("[*] Please connect your ESP32-CAM via USB now...")
        while not port:
            time.sleep(1)
            port = find_esp_port()
            print(".", end="", flush=True)
        print()

    print(f"\n[+] Found Target Port: {port}")
    print("[*] Compiling sketch with configured credentials (SSID: Pranshul)...")
    
    compile_cmd = [
        CLI_EXE, "compile",
        "--fqbn", "esp32:esp32:esp32cam",
        SKETCH_DIR
    ]
    res = subprocess.run(compile_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] Compilation failed:")
        print(res.stderr or res.stdout)
        return

    print("[+] Compilation Successful!")
    print(f"[*] Uploading firmware directly to {port}...")
    print("    (Note: If your board requires manual download mode, hold IO0 to GND and press RST)")

    upload_cmd = [
        CLI_EXE, "upload",
        "-p", port,
        "--fqbn", "esp32:esp32:esp32cam",
        SKETCH_DIR
    ]
    upload_res = subprocess.run(upload_cmd, capture_output=True, text=True)
    if upload_res.returncode != 0:
        print("[ERROR] Upload failed:")
        print(upload_res.stderr or upload_res.stdout)
        print("\nTip: Unplug and replug the USB cable, or ensure IO0 is grounded during flash.")
        return

    print("\n" + "=" * 60)
    print(" [SUCCESS] Firmware Flashed Successfully!")
    print("=" * 60)
    print("[*] Starting serial monitor to grab stream IP address...\n")
    
    # Run serial monitor
    import serial_monitor
    serial_monitor.monitor_serial(port)

if __name__ == "__main__":
    main()
