import cv2
import time
import argparse
import urllib.request
import subprocess
import platform
import os
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Measure ESP32-CAM WiFi latency and stream metrics")
    parser.add_argument("--ip", type=str, default="", help="ESP32-CAM IP address")
    parser.add_argument("--port", type=str, default="81", help="Stream port (default: 81)")
    return parser.parse_args()

def ping_host(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "4", host]
    try:
        output = subprocess.run(command, capture_output=True, text=True)
        return output.stdout
    except Exception as e:
        return str(e)

def main():
    args = parse_args()
    ip = args.ip
    if not ip:
        config_path = os.path.join(os.path.dirname(__file__), "camera_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                    ip = cfg.get("ip", "")
                    if ip:
                        print(f"[+] Loaded ESP32 IP from camera_config.json: {ip}")
            except Exception:
                pass
    if not ip:
        ip = input("Enter ESP32-CAM IP address (e.g. 192.168.1.50): ").strip()

    print(f"=== Latency & Network Diagnostics for {ip} ===")
    
    # 1. ICMP Ping Latency
    print("\n[1] ICMP Ping Round-Trip Time:")
    ping_out = ping_host(ip)
    print(ping_out)

    # 2. HTTP Frame Fetch Latency
    url = f"http://{ip}:{args.port}/stream"
    print(f"\n[2] Testing Video Stream at: {url}")
    
    from record_stream import RawSocketMJPEGReader

    cap = RawSocketMJPEGReader(url)
    if not cap.isOpened():
        # Fallback to port 80
        url_alt = f"http://{ip}/stream"
        print(f"[-] Could not open {url}. Trying {url_alt}...")
        cap = RawSocketMJPEGReader(url_alt)
        if not cap.isOpened():
            print("[ERROR] Cannot connect to camera stream.")
            return

    print("[+] Stream opened! Measuring frame-to-frame intervals (FPS and jitter)...")
    latencies = []
    prev_time = time.time()
    
    for i in range(100):
        t0 = time.time()
        ret, frame = cap.read()
        t1 = time.time()
        if not ret:
            print("[-] Frame read failed.")
            continue
        read_time = (t1 - t0) * 1000
        interval = (t1 - prev_time) * 1000
        prev_time = t1
        if i > 5: # Skip initial buffer warmup
            latencies.append((read_time, interval))
        time.sleep(0.01)

    cap.release()
    
    if latencies:
        avg_read = sum(x[0] for x in latencies) / len(latencies)
        avg_interval = sum(x[1] for x in latencies) / len(latencies)
        fps = 1000.0 / avg_interval if avg_interval > 0 else 0
        print("\n=== Stream Performance Summary ===")
        print(f"Average Frame Decode Time: {avg_read:.2f} ms")
        print(f"Average Frame Interval:    {avg_interval:.2f} ms")
        print(f"Effective Stream FPS:      {fps:.1f} FPS")
        if avg_interval < 70:
            print("Rating: EXCELLENT (Low latency, suitable for real-time tracking)")
        elif avg_interval < 150:
            print("Rating: GOOD (Acceptable for turret aiming with P/PI tuning)")
        else:
            print("Rating: HIGH LATENCY (Consider moving closer to router or reducing resolution)")

if __name__ == "__main__":
    main()
