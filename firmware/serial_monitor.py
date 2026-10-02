import serial
import serial.tools.list_ports
import time
import re
import json
import os
import sys

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "camera_config.json")

def find_esp_port():
    ports = list(serial.tools.list_ports.comports())
    # Exclude standard bluetooth links if possible
    valid_ports = [p for p in ports if "bluetooth" not in p.description.lower()]
    if valid_ports:
        return valid_ports[0].device
    return None

def monitor_serial(port_name=None, baudrate=115200):
    print("=" * 60)
    print("  ESP32-CAM Pure Python Serial Monitor & IP Auto-Discovery")
    print("=" * 60)

    if not port_name:
        port_name = find_esp_port()

    while not port_name:
        print("[!] No USB Serial port detected yet.")
        print("[*] Please connect your ESP32 via USB (ensure it is a data cable).")
        print("[*] Waiting for USB port connection (checking every 2 seconds)...")
        time.sleep(2)
        port_name = find_esp_port()

    print(f"\n[+] Connected to USB Serial Port: {port_name} at {baudrate} baud.")
    print("[*] Reading serial output... Press Ctrl+C to exit.")
    print("[*] (Tip: You can press the RST/EN button on your ESP32 to restart and print the IP address)\n")

    try:
        ser = serial.Serial(port_name, baudrate, timeout=1, dsrdtr=False, rtscts=False)
        ser.dtr = False
        ser.rts = False
    except Exception as e:
        print(f"[ERROR] Could not open port {port_name}: {e}")
        return None

    ip_regex = re.compile(r"http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    alt_ip_regex = re.compile(r"\b(?:IP|ip)[\s:=]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")

    found_ip = None
    try:
        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                print(f"[ESP32] {line}")
                
                # Check for IP
                m = ip_regex.search(line) or alt_ip_regex.search(line)
                if m:
                    found_ip = m.group(1)
                    print("\n" + "*" * 60)
                    print(f" [SUCCESS] Discovered ESP32-CAM IP: {found_ip}")
                    print("*" * 60 + "\n")
                    
                    # Save to config
                    cfg = {"ip": found_ip, "port": 81, "stream_url": f"http://{found_ip}:81/stream"}
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(cfg, f, indent=2)
                    print(f"[+] Saved IP configuration to: {CONFIG_FILE}")
                    break
    except KeyboardInterrupt:
        print("\n[!] Serial monitoring stopped by user.")
    finally:
        ser.close()

    return found_ip

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else None
    monitor_serial(port)
