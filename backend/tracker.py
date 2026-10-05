"""
Agesis EYE - Core Video Stream Reader and YOLO Inference Engine
High-performance decoupled architecture for real-time edge tracking.
"""

import os
import sys
import time
import json
import socket
import threading
import numpy as np
import cv2
import requests
from concurrent.futures import ThreadPoolExecutor

# Try loading ONNX Runtime or Ultralytics YOLO
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

try:
    from ultralytics import YOLO
    import torch
    torch.set_num_threads(4)
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False


def auto_discover_esp32_ip(subnet_prefix=None):
    """Dynamically probe USB Serial ports and local network subnets on port 81."""
    # 0. Check USB serial ports first (Direct ESP32-CAM USB connector)
    try:
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports() if "bluetooth" not in p.description.lower()]
        if ports:
            if "COM15" in ports:
                return "COM15"
            return ports[0]
    except Exception:
        pass

    subnets = []
    if subnet_prefix:
        subnets.append(subnet_prefix)

    # 1. Check default ESP32 SoftAP IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex(("192.168.4.1", 81)) == 0:
            s.close()
            return "http://192.168.4.1:81/stream"
        s.close()
    except Exception:
        pass

    # 2. Extract host interface subnets
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        parts = host_ip.split(".")
        if len(parts) == 4:
            sub = f"{parts[0]}.{parts[1]}.{parts[2]}"
            if sub not in subnets:
                subnets.append(sub)
    except Exception:
        pass

    for fallback in ["192.168.1", "192.168.0", "10.96.117"]:
        if fallback not in subnets:
            subnets.append(fallback)

    def check_ip(ip):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.12)
        try:
            if s.connect_ex((ip, 81)) == 0:
                return ip
        except Exception:
            pass
        finally:
            s.close()
        return None

    for sub in subnets:
        with ThreadPoolExecutor(max_workers=50) as ex:
            ips = [f"{sub}.{i}" for i in range(1, 255)]
            results = [r for r in ex.map(check_ip, ips) if r]
            if results:
                return f"http://{results[0]}:81/stream"
    return None


class ZeroLagStreamReader:
    """
    Consistent, zero-latency stream reader that drains frames continuously.
    Supports:
    1. HTTP MJPEG stream (e.g., 'http://192.168.4.1:81/stream')
    2. USB Serial Direct Stream ('usb', 'serial', 'COMx')
    3. DirectShow / V4L2 webcam index (0, 1, 2)
    """
    def __init__(self, source):
        self.source = str(source) if source is not None else "0"
        self.latest_frame = None
        self.frame_id = 0
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.fps = 0.0
        
        src_lower = self.source.lower().strip()
        self.is_url = src_lower.startswith("http")
        self.is_serial = src_lower in ("usb", "serial", "auto") or src_lower.startswith("com")
        self._thread = None
        self.start()

    def start(self):
        self.running = True
        if self.is_url:
            self._thread = threading.Thread(target=self._requests_mjpeg_worker, daemon=True)
        elif self.is_serial:
            self._thread = threading.Thread(target=self._serial_worker, daemon=True)
        else:
            self._thread = threading.Thread(target=self._cv2_worker, daemon=True)
        self._thread.start()

    def _serial_worker(self):
        """Read JPEG frames directly from ESP32-CAM over USB Serial UART."""
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            print("[STREAM] pyserial not available for USB video streaming.")
            return

        port = self.source
        if port.lower() in ("usb", "serial", "auto"):
            ports = [p for p in serial.tools.list_ports.comports() if "bluetooth" not in p.description.lower()]
            if ports:
                port = ports[0].device
            else:
                port = "COM15"

        print(f"[STREAM] Connecting to ESP32-CAM USB Serial on {port}...")
        while self.running:
            ser = None
            try:
                ser = serial.Serial()
                ser.port = port
                ser.baudrate = 115200
                ser.timeout = 0.2
                ser.open()
                try:
                    ser.dtr = False
                    ser.rts = False
                except Exception:
                    pass
                self.ser_conn = ser

                self.connected = True
                print(f"[STREAM] Connected to {port} for USB camera stream.")
                time.sleep(0.2)
                # Request ESP32 to activate serial video streaming
                ser.write(b"STREAM_ON\n")
                ser.flush()
                
                bytes_buf = b""
                fc, t0 = 0, time.time()
                last_ping_time = time.time()

                while self.running:
                    now = time.time()
                    # Re-send STREAM_ON every 1.5s if no frames have arrived
                    if now - last_ping_time > 1.5:
                        try:
                            ser.write(b"STREAM_ON\n")
                            ser.flush()
                        except Exception:
                            pass
                        last_ping_time = now

                    waiting = ser.in_waiting
                    if not waiting:
                        time.sleep(0.004)
                        continue
                    chunk = ser.read(waiting)
                    if not chunk:
                        continue
                    if len(bytes_buf) == 0:
                        print(f"[SERIAL] Received first {len(chunk)} bytes from ESP32: {chunk[:40]}")
                    bytes_buf += chunk
                    
                    # Zero-Lag Drain: scan forward to find the LATEST complete frame and skip stale backlog
                    last_valid_start = -1
                    last_valid_len = 0
                    search_pos = 0

                    while True:
                        idx = bytes_buf.find(b"--FRAME:", search_pos)
                        if idx == -1:
                            break
                        end_hdr = bytes_buf.find(b"\n", idx)
                        if end_hdr != -1:
                            hdr = bytes_buf[idx:end_hdr].decode("ascii", errors="ignore")
                            try:
                                flen = int(hdr.split(":")[1].strip())
                                if len(bytes_buf) >= end_hdr + 1 + flen:
                                    last_valid_start = end_hdr + 1
                                    last_valid_len = flen
                                    search_pos = end_hdr + 1 + flen
                                    continue
                            except Exception:
                                pass
                        search_pos = idx + 8

                    if last_valid_start != -1:
                        # Decode only the newest complete frame and discard older backlog
                        img_data = bytes_buf[last_valid_start : last_valid_start + last_valid_len]
                        bytes_buf = bytes_buf[last_valid_start + last_valid_len:]
                        frame = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            if self.frame_id == 0:
                                print(f"[STREAM] First frame successfully decoded! ({frame.shape[1]}x{frame.shape[0]})")
                            with self.lock:
                                self.latest_frame = frame
                                self.frame_id += 1
                                self.connected = True
                            fc += 1
                            last_ping_time = now
                            if now - t0 >= 1.0:
                                self.fps = fc / (now - t0)
                                fc, t0 = 0, now
                        continue

                    # Fallback: Raw JPEG SOI/EOI delimiters
                    a = bytes_buf.rfind(b"\xff\xd8")  # Find most recent JPEG start
                    if a != -1:
                        b = bytes_buf.find(b"\xff\xd9", a)  # Find matching JPEG end
                        if b != -1 and b > a:
                            jpg = bytes_buf[a:b+2]
                            bytes_buf = bytes_buf[b+2:]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                with self.lock:
                                    self.latest_frame = frame
                                    self.frame_id += 1
                                    self.connected = True
                                fc += 1
                                now = time.time()
                                if now - t0 >= 1.0:
                                    self.fps = fc / (now - t0)
                                    fc, t0 = 0, now
                    elif len(bytes_buf) > 65536:
                        bytes_buf = bytes_buf[-8192:]
            except Exception as e:
                print(f"[STREAM EXCEPTION] {e}")
                self.connected = False
                time.sleep(1.0)
            finally:
                if ser:
                    try:
                        ser.close()
                    except Exception:
                        pass
                self.ser_conn = None

    def _cv2_worker(self):
        src = int(self.source) if str(self.source).isdigit() else self.source
        if isinstance(src, int):
            # On Windows, cv2.CAP_DSHOW provides fastest DirectShow access
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            cap = cv2.VideoCapture(src)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.connected = cap.isOpened()
        fc, t0 = 0, time.time()

        while self.running:
            ret, frame = cap.read()
            if ret and frame is not None:
                with self.lock:
                    self.latest_frame = frame
                    self.frame_id += 1
                    self.connected = True
                fc += 1
                now = time.time()
                if now - t0 >= 1.0:
                    self.fps = fc / (now - t0)
                    fc, t0 = 0, now
            else:
                self.connected = False
                time.sleep(0.01)
        cap.release()

    def _requests_mjpeg_worker(self):
        sess = requests.Session()
        while self.running:
            try:
                resp = sess.get(self.source, stream=True, timeout=(4, 8))
                resp.raise_for_status()
                self.connected = True
                bytes_buf = b""
                fc, t0 = 0, time.time()

                for chunk in resp.iter_content(chunk_size=4096):
                    if not self.running:
                        break
                    bytes_buf += chunk
                    a = bytes_buf.find(b"\xff\xd8")  # JPEG Start
                    b = bytes_buf.find(b"\xff\xd9")  # JPEG End
                    if a != -1 and b != -1:
                        if b > a:
                            jpg = bytes_buf[a:b+2]
                            bytes_buf = bytes_buf[b+2:]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                with self.lock:
                                    self.latest_frame = frame
                                    self.frame_id += 1
                                fc += 1
                                now = time.time()
                                if now - t0 >= 1.0:
                                    self.fps = fc / (now - t0)
                                    fc, t0 = 0, now
                        else:
                            bytes_buf = bytes_buf[a:]
            except Exception:
                self.connected = False
                time.sleep(1.0)

    def get_latest(self):
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame, self.frame_id
            return None, 0

    def write_serial(self, data: bytes):
        """Write serial data over the active USB connection."""
        if getattr(self, "ser_conn", None) and getattr(self.ser_conn, "is_open", False):
            try:
                self.ser_conn.write(data)
                return True
            except Exception:
                pass
        return False

    def release(self):
        self.running = False
        if getattr(self, "ser_conn", None):
            try:
                self.ser_conn.close()
            except Exception:
                pass
            self.ser_conn = None


class BalloonTracker:
    """YOLO detection and tracking engine with adaptive peripheral FOV thresholding."""
    def __init__(self, model_path, imgsz=384, conf=0.22, iou=0.45, lock_threshold=2, enhance=True):
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf
        self.iou = iou
        self.lock_threshold = lock_threshold
        self.enhance = enhance

        # Telemetry State
        self.best_box = None
        self.locked = False
        self.streak = 0
        self.latency_ms = 0.0
        self.infer_fps = 0.0
        self.target_pos = "CENTER"
        self.dx = 0
        self.dy = 0
        self.target_conf = 0.0

        # Model Backend setup
        self.is_onnx = str(model_path).endswith(".onnx")
        self.ort_session = None
        self.yolo_model = None

        if self.is_onnx and HAS_ONNX:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 4
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.ort_session = ort.InferenceSession(self.model_path, opts, providers=["CPUExecutionProvider"])
            self.input_name = self.ort_session.get_inputs()[0].name
        elif HAS_YOLO:
            self.yolo_model = YOLO(self.model_path)
        else:
            raise RuntimeError("Neither ONNX Runtime nor Ultralytics is available!")

        # CLAHE Domain Transform filter
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def apply_ep_clahe(self, img_bgr):
        """Edge-Preserving CLAHE transform and auto-exposure for robust low-contrast balloon detection."""
        mean_v = np.mean(img_bgr)
        if mean_v < 70:
            scale = min(2.5, 100.0 / max(mean_v, 8.0))
            img_bgr = cv2.convertScaleAbs(img_bgr, alpha=scale, beta=10)
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_clahe = self.clahe.apply(l)
        enhanced_lab = cv2.merge((l_clahe, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def process_frame(self, frame):
        """Run detection on a single frame and return annotated frame + telemetry dict."""
        t_start = time.perf_counter()
        h_orig, w_orig = frame.shape[:2]
        cx_optical, cy_optical = w_orig // 2, h_orig // 2

        img_in = frame
        if self.enhance:
            img_in = self.apply_ep_clahe(frame)

        boxes = []
        if self.ort_session is not None:
            # High-speed ONNX Inference Pipeline
            img_resized = cv2.resize(img_in, (self.imgsz, self.imgsz))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            input_tensor = np.transpose(img_rgb, (2, 0, 1)).astype(np.float32) / 255.0
            input_tensor = np.expand_dims(input_tensor, axis=0)

            outputs = self.ort_session.run(None, {self.input_name: input_tensor})
            preds = np.squeeze(outputs[0])  # Shape [5, 3024]
            if preds.shape[0] < preds.shape[1]:
                preds = preds.T

            # Format: [cx, cy, w, h, conf]
            cx_p = preds[:, 0]
            cy_p = preds[:, 1]
            w_p = preds[:, 2]
            h_p = preds[:, 3]
            confs = preds[:, 4]

            # Peripheral edge adaptive confidence threshold
            xc_norm = cx_p / self.imgsz
            adaptive_thresh = np.where((xc_norm < 0.15) | (xc_norm > 0.85), max(0.14, self.conf - 0.08), self.conf)
            mask = confs >= adaptive_thresh

            if np.any(mask):
                valid_cx = cx_p[mask]
                valid_cy = cy_p[mask]
                valid_w = w_p[mask]
                valid_h = h_p[mask]
                valid_confs = confs[mask]

                sx = w_orig / self.imgsz
                sy = h_orig / self.imgsz

                x1s = ((valid_cx - valid_w / 2) * sx).astype(int)
                y1s = ((valid_cy - valid_h / 2) * sy).astype(int)
                x2s = ((valid_cx + valid_w / 2) * sx).astype(int)
                y2s = ((valid_cy + valid_h / 2) * sy).astype(int)

                # Flexible aspect ratio filter: supports round, oval, and oblong balloons
                ars = valid_w / np.maximum(valid_h, 1e-4)
                ar_mask = (ars >= 0.25) & (ars <= 3.50)

                nms_boxes = []
                nms_confs = []
                for x1, y1, x2, y2, c, ok in zip(x1s, y1s, x2s, y2s, valid_confs, ar_mask):
                    if ok:
                        x1 = max(0, min(x1, w_orig - 1))
                        y1 = max(0, min(y1, h_orig - 1))
                        x2 = max(0, min(x2, w_orig - 1))
                        y2 = max(0, min(y2, h_orig - 1))
                        nms_boxes.append([x1, y1, x2 - x1, y2 - y1])
                        nms_confs.append(float(c))

                if nms_boxes:
                    indices = cv2.dnn.NMSBoxes(nms_boxes, nms_confs, score_threshold=0.14, nms_threshold=self.iou)
                    if len(indices) > 0:
                        for idx in indices.flatten():
                            bx, by, bw, bh = nms_boxes[idx]
                            boxes.append((bx, by, bx + bw, by + bh, nms_confs[idx]))

        elif self.yolo_model is not None:
            results = self.yolo_model.predict(img_in, imgsz=self.imgsz, conf=self.conf * 0.7,
                                              iou=self.iou, verbose=False)
            if results and len(results[0].boxes):
                for b in results[0].boxes:
                    x1, y1, x2, y2 = map(int, b.xyxy[0])
                    c = float(b.conf[0])
                    xc = ((x1 + x2) / 2) / w_orig
                    min_conf = max(0.18, self.conf - 0.15) if (xc < 0.18 or xc > 0.82) else self.conf
                    if c >= min_conf:
                        boxes.append((x1, y1, x2, y2, c))

        # Select highest-confidence detection
        if boxes:
            self.best_box = max(boxes, key=lambda b: b[4])
            self.streak = min(self.streak + 1, 20)
            self.locked = self.streak >= self.lock_threshold
        else:
            self.best_box = None
            self.streak = max(0, self.streak - 1)
            self.locked = False

        self.latency_ms = (time.perf_counter() - t_start) * 1000.0

        # Compute Aiming Offsets
        if self.best_box is not None:
            x1, y1, x2, y2, conf_val = self.best_box
            bx_c = (x1 + x2) // 2
            by_c = (y1 + y2) // 2
            self.dx = bx_c - cx_optical
            self.dy = by_c - cy_optical
            self.target_conf = float(conf_val)

            if bx_c < 0.18 * w_orig:
                self.target_pos = "EXTREME LEFT"
            elif bx_c > 0.82 * w_orig:
                self.target_pos = "EXTREME RIGHT"
            else:
                self.target_pos = "CENTER"
        else:
            self.dx = 0
            self.dy = 0
            self.target_conf = 0.0
            self.target_pos = "NONE"

        # Render Minimalist Tactical Target Overlays
        annotated = frame.copy()

        # Ultra-minimal center optical crosshair (subtle gray)
        cv2.drawMarker(annotated, (cx_optical, cy_optical), (60, 60, 60),
                       markerType=cv2.MARKER_CROSS, markerSize=18, thickness=1)

        # Minimalist Bounding Box (Blood Red / Crimson Tactical Corners)
        if self.best_box is not None:
            x1, y1, x2, y2, c = self.best_box
            bx_c = (x1 + x2) // 2
            by_c = (y1 + y2) // 2

            # Blood Red (BGR): Active Lock = (30, 20, 255) Vibrant Red, Acquiring = (20, 100, 240) Ember Red
            color = (35, 25, 255) if self.locked else (20, 110, 245)
            
            # 1. Subtle thin bounding frame
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

            # 2. Sleek Corner Brackets (sexy tactical reticle look)
            corner_len = max(6, min(14, (x2 - x1) // 4, (y2 - y1) // 4))
            t = 2  # thickness
            # Top-Left
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), color, t)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), color, t)
            # Top-Right
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), color, t)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), color, t)
            # Bottom-Left
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), color, t)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), color, t)
            # Bottom-Right
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), color, t)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), color, t)

            # Target Center Reticle Point
            cv2.drawMarker(annotated, (bx_c, by_c), color, markerType=cv2.MARKER_CROSS, markerSize=10, thickness=1)

            # Minimalist Clean Tag (no bulky background, sharp text)
            tag_text = f"TRGT {c*100:.0f}%"
            cv2.putText(annotated, tag_text, (x1, max(12, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)

        telemetry = {
            "locked": bool(self.locked),
            "streak": int(self.streak),
            "lock_threshold": int(self.lock_threshold),
            "dx": int(self.dx),
            "dy": int(self.dy),
            "conf": float(round(self.target_conf, 3)),
            "target_pos": str(self.target_pos),
            "latency_ms": float(round(self.latency_ms, 1)),
            "enhance": bool(self.enhance),
            "conf_threshold": float(self.conf),
            "has_target": bool(self.best_box is not None)
        }

        return annotated, telemetry
