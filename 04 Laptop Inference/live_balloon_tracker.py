"""
Agesis EYE - Stage 04: Real-time Balloon Detector & Tracker (High-Performance Zero-Lag)
Decoupled multi-threaded architecture:
- Thread 1: High-speed Stream Reader (uses requests session + chunked buffer drain, zero latency)
- Thread 2: Asynchronous YOLO Worker (runs PyTorch with optimized thread scheduling)
- Main Thread: Real-time 30+ FPS HUD display & Aiming Reticle
"""

import cv2
import threading
import time
import argparse
import os
import sys
import json
import socket
import numpy as np
import requests
import torch
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO

# Optimize PyTorch CPU execution for low latency
torch.set_num_threads(4)


def auto_discover_esp32_ip(subnet_prefix="10.96.117"):
    """Quickly probe the subnet on port 81 to discover ESP32 camera IP."""
    print(f"[*] Scanning {subnet_prefix}.1..254 for ESP32-CAM stream on port 81...")
    
    def check_ip(i):
        ip = f"{subnet_prefix}.{i}"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            if s.connect_ex((ip, 81)) == 0:
                return ip
        except Exception:
            pass
        finally:
            s.close()
        return None

    with ThreadPoolExecutor(max_workers=50) as ex:
        results = [r for r in ex.map(check_ip, range(1, 255)) if r]
        
    if results:
        print(f"[+] Found ESP32 camera at: http://{results[0]}:81/stream")
        return f"http://{results[0]}:81/stream"
    return None


class ZeroLagStreamReader:
    """Consistently drains the ESP32-CAM stream via requests and keeps TCP buffer empty."""
    def __init__(self, source):
        self.source = source
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.fps = 0.0
        self.is_url = isinstance(source, str) and source.startswith("http")

        if self.is_url:
            self._thread = threading.Thread(target=self._requests_mjpeg_worker, daemon=True)
        else:
            self._thread = threading.Thread(target=self._cv2_worker, daemon=True)
        self._thread.start()

    def _cv2_worker(self):
        src = int(self.source) if str(self.source).isdigit() else self.source
        cap = cv2.VideoCapture(src)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.connected = cap.isOpened()
        fc, t0 = 0, time.time()

        while self.running:
            ret, frame = cap.read()
            if ret and frame is not None:
                with self.lock:
                    self.latest_frame = frame
                fc += 1
                now = time.time()
                if now - t0 >= 1.0:
                    self.fps = fc / (now - t0)
                    fc, t0 = 0, now
            else:
                time.sleep(0.01)
        cap.release()

    def _requests_mjpeg_worker(self):
        sess = requests.Session()
        while self.running:
            try:
                print(f"[*] Connecting to ESP32 stream: {self.source}")
                resp = sess.get(self.source, stream=True, timeout=(4, 8))
                resp.raise_for_status()
                self.connected = True
                print(f"[+] Connected to stream successfully! Draining frames at maximum speed.")

                buf = b''
                fc, t0 = 0, time.time()

                for chunk in resp.iter_content(chunk_size=4096):
                    if not self.running:
                        break
                    buf += chunk

                    # Extract all complete JPEGs and keep only the freshest
                    fresh_frame = None
                    while True:
                        a = buf.find(b'\xff\xd8')
                        if a == -1:
                            buf = buf[-2:] if len(buf) > 2 else buf
                            break
                        b = buf.find(b'\xff\xd9', a + 2)
                        if b == -1:
                            buf = buf[a:]
                            break

                        jpg = buf[a:b + 2]
                        buf = buf[b + 2:]
                        decoded = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                        if decoded is not None:
                            fresh_frame = decoded
                            fc += 1

                    if fresh_frame is not None:
                        with self.lock:
                            self.latest_frame = fresh_frame

                    now = time.time()
                    if now - t0 >= 1.0:
                        self.fps = fc / (now - t0)
                        fc, t0 = 0, now

            except Exception as e:
                self.connected = False
                if self.running:
                    print(f"[!] Stream connection error ({e}). Auto-retrying in 1.5s...")
                    time.sleep(1.5)
            finally:
                try:
                    resp.close()
                except Exception:
                    pass

    def get_latest(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def release(self):
        self.running = False


def apply_ep_clahe(frame_bgr):
    """Optimal domain transform: 2.1ms bilateral noise reduction + CLAHE contrast boost."""
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_denoised = cv2.bilateralFilter(l, d=5, sigmaColor=25, sigmaSpace=25)
    clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_denoised)
    return cv2.cvtColor(cv2.merge([l_enhanced, a, b]), cv2.COLOR_LAB2BGR)


class YOLOTrackerWorker:
    """Asynchronous worker that runs inference without blocking video display."""
    def __init__(self, model_path, imgsz=384, conf=0.40, iou=0.45, lock_frames=3, enhance=False):
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf
        self.iou = iou
        self.lock_threshold = lock_frames
        self.enhance = enhance
        
        print(f"[*] Loading PyTorch YOLO Model: {model_path} (imgsz={imgsz})")
        self.model = YOLO(model_path)
        
        # Warmup model
        dummy = np.zeros((240, 320, 3), dtype=np.uint8)
        self.model.predict(dummy, imgsz=self.imgsz, verbose=False)
        print("[+] Model loaded and warmed up.")

        self.running = True
        self.latest_input = None
        self.input_lock = threading.Lock()
        
        self.output_lock = threading.Lock()
        self.best_box = None
        self.streak = 0
        self.locked = False
        self.latency_ms = 0.0
        self.infer_fps = 0.0

        self._thread = threading.Thread(target=self._infer_loop, daemon=True)
        self._thread.start()

    def set_frame(self, frame):
        with self.input_lock:
            self.latest_input = frame

    def _infer_loop(self):
        fc = 0
        t0 = time.time()

        while self.running:
            target_frame = None
            with self.input_lock:
                if self.latest_input is not None:
                    target_frame = self.latest_input
                    self.latest_input = None  # consume freshest frame

            if target_frame is None:
                time.sleep(0.003)
                continue

            # Apply EP-CLAHE domain transform if enabled
            if self.enhance:
                target_frame = apply_ep_clahe(target_frame)

            t_start = time.perf_counter()
            # Predict at lower base confidence to catch edge-truncated balloons
            base_conf = max(0.18, min(0.25, self.conf - 0.15))
            results = self.model.predict(
                target_frame,
                imgsz=self.imgsz,
                conf=base_conf,
                iou=self.iou,
                verbose=False
            )[0]
            dt = (time.perf_counter() - t_start) * 1000

            boxes = results.boxes
            fh, fw = target_frame.shape[:2]
            valid_boxes = []

            for b in boxes:
                c = float(b.conf[0])
                bx1, by1, bx2, by2 = map(int, b.xyxy[0].tolist())
                bw = max(1, bx2 - bx1)
                bh = max(1, by2 - by1)
                bcx = (bx1 + bx2) // 2
                bcy = (by1 + by2) // 2

                # Check if balloon is in extreme periphery (within 18% of border)
                is_near_edge = (bcx < 0.18 * fw) or (bcx > 0.82 * fw) or (by1 < 0.12 * fh) or (by2 > 0.88 * fh)

                # Aspect ratio check (tolerant to lens edge distortion: 0.60 to 1.60)
                aspect = bw / float(bh)
                if not (0.55 <= aspect <= 1.70):
                    continue

                # Adaptive confidence threshold: center requires full conf, edge allows lower threshold
                thresh = base_conf if is_near_edge else self.conf
                if c >= thresh:
                    valid_boxes.append((bx1, by1, bx2, by2, c, is_near_edge))

            with self.output_lock:
                self.latency_ms = dt
                if len(valid_boxes) > 0:
                    best = max(valid_boxes, key=lambda x: x[4])
                    self.best_box = best[:5]
                    self.streak += 1
                    self.locked = self.streak >= self.lock_threshold
                else:
                    self.streak = max(0, self.streak - 1)
                    if self.streak == 0:
                        self.best_box = None
                        self.locked = False

            fc += 1
            now = time.time()
            if now - t0 >= 1.0:
                self.infer_fps = fc / (now - t0)
                fc, t0 = 0, now

    def get_detection(self):
        with self.output_lock:
            return self.best_box, self.locked, self.streak, self.latency_ms, self.infer_fps

    def release(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="Agesis EYE Live Balloon Tracker (Zero Lag)")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Search for model weights in order of preference (students: 04 Laptop Inference/models, root: Model)
    default_candidates = [
        os.path.join(script_dir, "models", "agesis06.onnx"),
        os.path.join(script_dir, "models", "agesis06.pt"),
        os.path.join(script_dir, "models", "best.onnx"),
        os.path.join(script_dir, "models", "best.pt"),
        os.path.join(project_root, "Model", "agesis06.onnx"),
        os.path.join(project_root, "Model", "agesis06.pt"),
        os.path.join(project_root, "Model", "best.pt"),
    ]
    default_model = next((p for p in default_candidates if os.path.exists(p)), default_candidates[0])
    
    # Read configured stream URL
    cfg_candidates = [
        os.path.join(project_root, "01 Camera Stream and Record", "camera_config.json"),
        os.path.join(script_dir, "camera_config.json"),
        os.path.join(os.getcwd(), "01 Camera Stream and Record", "camera_config.json")
    ]
    cfg_path = next((p for p in cfg_candidates if os.path.exists(p)), cfg_candidates[0])
    default_url = "http://10.96.117.1:81/stream"
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
                default_url = cfg.get("stream_url", default_url)
        except Exception:
            pass

    parser.add_argument("--model", type=str, default=default_model, help="Path to best model (.onnx or .pt)")
    parser.add_argument("--source", type=str, default=default_url, help="Stream URL or 0 for webcam")
    parser.add_argument("--imgsz", type=int, default=384, help="Inference resolution (320, 384, or 480)")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="IoU NMS threshold")
    parser.add_argument("--lock-frames", type=int, default=3, help="Frames for target lock")
    parser.add_argument("--enhance", action="store_true", help="Enable EP-CLAHE domain transform")
    args = parser.parse_args()

    # Verify stream accessibility, or auto-discover
    stream_url = args.source
    if stream_url.startswith("http"):
        try:
            r = requests.get(stream_url, timeout=1.5, stream=True)
            r.close()
            print(f"[+] Verified stream connection at {stream_url}")
        except Exception:
            print(f"[-] Configured URL {stream_url} unreachable. Attempting auto-discovery...")
            discovered = auto_discover_esp32_ip()
            if discovered:
                stream_url = discovered
                try:
                    with open(cfg_path, "w") as f:
                        json.dump({
                            "stream_url": stream_url,
                            "snapshot_url": stream_url.replace(":81/stream", "/capture")
                        }, f, indent=2)
                except Exception:
                    pass

    print(f"[+] Final Video Stream Source : {stream_url}")
    print(f"[+] Model Weights             : {args.model}")
    print(f"[+] Inference Input Resolution: {args.imgsz}")
    print(f"[+] EP-CLAHE Domain Transform : {'ENABLED' if args.enhance else 'OFF (Press e to toggle)'}")

    reader = ZeroLagStreamReader(stream_url)
    worker = YOLOTrackerWorker(args.model, imgsz=args.imgsz, conf=args.conf, iou=args.iou,
                               lock_frames=args.lock_frames, enhance=args.enhance)

    # Wait for initial stream frame
    print("[*] Waiting for video stream frames...")
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if reader.get_latest() is not None:
            break
        time.sleep(0.1)

    if reader.get_latest() is None:
        print(f"\n[-] Please make sure the ESP32-CAM is powered on and connected to the WiFi hotspot.")
        reader.release()
        worker.release()
        return

    window_name = "Agesis EYE - ESP32-CAM Balloon Tracker (Zero Lag)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    print("\n" + "="*58)
    print("  AGESIS EYE - ZERO-LAG LIVE TRACKING ACTIVE")
    print("  Controls: [q] Quit  [e] Toggle EP-CLAHE Domain  [+] Conf+  [-] Conf-  [s] Snap")
    print("="*58 + "\n")

    prev_time = time.perf_counter()
    display_fps = 0.0
    snap_idx = 0

    try:
        while True:
            frame = reader.get_latest()
            if frame is None:
                time.sleep(0.005)
                continue

            # Pass freshest frame to async YOLO worker
            worker.set_frame(frame)

            # Get latest detection instantly without blocking!
            best_box, locked, streak, lat_ms, infer_fps = worker.get_detection()

            h, w = frame.shape[:2]
            cx_center, cy_center = w // 2, h // 2
            annotated = frame.copy()

            # Aiming reticle (Center of camera view)
            cv2.drawMarker(annotated, (cx_center, cy_center), (90, 90, 90),
                           markerType=cv2.MARKER_CROSS, markerSize=20, thickness=1)
            cv2.circle(annotated, (cx_center, cy_center), 25, (70, 70, 70), 1)

            if best_box is not None:
                x1, y1, x2, y2, conf = best_box
                bx_c = (x1 + x2) // 2
                by_c = (y1 + y2) // 2
                dx = bx_c - cx_center
                dy = by_c - cy_center

                color = (0, 255, 0) if locked else (0, 165, 255)
                box_thickness = 3 if locked else 2

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, box_thickness)
                cv2.circle(annotated, (bx_c, by_c), 5, (0, 0, 255), -1)
                cv2.line(annotated, (cx_center, cy_center), (bx_c, by_c), (0, 255, 255), 1)

                edge_tag = ""
                if bx_c < 0.18 * w:
                    edge_tag = " [EXTREME LEFT]"
                elif bx_c > 0.82 * w:
                    edge_tag = " [EXTREME RIGHT]"

                lbl_text = f"BALLOON {conf*100:.1f}%{edge_tag} | dX:{dx:+d} dY:{dy:+d}"
                (lw, lh), _ = cv2.getTextSize(lbl_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(annotated, (x1, y1 - 20), (x1 + lw + 6, y1), color, -1)
                cv2.putText(annotated, lbl_text, (x1 + 3, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

            # Display FPS calculation
            t_now = time.perf_counter()
            dt = t_now - prev_time
            if dt > 0:
                display_fps = 0.9 * display_fps + 0.1 * (1.0 / dt)
            prev_time = t_now

            # Extreme FOV boundary guides (calibrates user view from extreme left to extreme right)
            left_lim = int(0.12 * w)
            right_lim = int(0.88 * w)
            cv2.line(annotated, (left_lim, 32), (left_lim, h - 10), (45, 45, 45), 1, cv2.LINE_AA)
            cv2.line(annotated, (right_lim, 32), (right_lim, h - 10), (45, 45, 45), 1, cv2.LINE_AA)

            # Top HUD Bar
            cv2.rectangle(annotated, (0, 0), (w, 28), (20, 20, 20), -1)
            if locked:
                status_txt = f"LOCKED ({streak})"
                s_color = (0, 255, 0)
            elif streak > 0:
                status_txt = f"ACQUIRING ({streak}/{worker.lock_threshold})"
                s_color = (0, 165, 255)
            else:
                status_txt = "SEARCHING..."
                s_color = (0, 0, 255)

            cv2.putText(annotated, status_txt, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.48, s_color, 2)
            enh_badge = " [EP-CLAHE: ON]" if worker.enhance else ""
            perf_txt = f"Cam:{reader.fps:.0f}FPS | Disp:{display_fps:.0f}FPS | Infer:{lat_ms:.0f}ms{enh_badge} | Conf:{worker.conf:.2f}"
            (pw, _), _ = cv2.getTextSize(perf_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.putText(annotated, perf_txt, (w - pw - 6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (220, 220, 220), 1)

            cv2.imshow(window_name, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            elif key == ord('e'):
                worker.enhance = not worker.enhance
                print(f"[+] Domain Enhancement (EP-CLAHE): {'ON' if worker.enhance else 'OFF'}")
            elif key in (ord('+'), ord('=')):
                worker.conf = min(0.95, worker.conf + 0.05)
                print(f"[+] Conf threshold: {worker.conf:.2f}")
            elif key in (ord('-'), ord('_')):
                worker.conf = max(0.10, worker.conf - 0.05)
                print(f"[-] Conf threshold: {worker.conf:.2f}")
            elif key == ord('s'):
                os.makedirs("scratch", exist_ok=True)
                snap_path = f"scratch/esp32_snap_{snap_idx:03d}.jpg"
                cv2.imwrite(snap_path, annotated)
                print(f"[+] Snapshot saved: {snap_path}")
                snap_idx += 1

    finally:
        reader.release()
        worker.release()
        cv2.destroyAllWindows()
        print("[+] Live tracker stopped cleanly.")


if __name__ == "__main__":
    main()
