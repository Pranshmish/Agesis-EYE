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


def auto_discover_esp32_ip(subnet_prefix="10.96.117"):
    """Quickly probe the subnet on port 81 to discover ESP32 camera IP."""
    def check_ip(i):
        ip = f"{subnet_prefix}.{i}"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
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
        return f"http://{results[0]}:81/stream"
    return None


class ZeroLagStreamReader:
    """Consistent, zero-latency stream reader that drains MJPEG buffers continuously."""
    def __init__(self, source):
        self.source = source
        self.latest_frame = None
        self.frame_id = 0
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.fps = 0.0
        self.is_url = isinstance(source, str) and source.startswith("http")
        self._thread = None
        self.start()

    def start(self):
        self.running = True
        if self.is_url:
            self._thread = threading.Thread(target=self._requests_mjpeg_worker, daemon=True)
        else:
            self._thread = threading.Thread(target=self._cv2_worker, daemon=True)
        self._thread.start()

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

    def release(self):
        self.running = False


class BalloonTracker:
    """YOLO detection and tracking engine with adaptive peripheral FOV thresholding."""
    def __init__(self, model_path, imgsz=384, conf=0.35, iou=0.45, lock_threshold=3, enhance=False):
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
        """Edge-Preserving CLAHE transform for robust low-contrast balloon detection."""
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
            adaptive_thresh = np.where((xc_norm < 0.18) | (xc_norm > 0.82), max(0.18, self.conf - 0.15), self.conf)
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

                # Aspect ratio filter for realistic balloon geometry
                ars = valid_w / np.maximum(valid_h, 1e-4)
                ar_mask = (ars >= 0.50) & (ars <= 1.80)

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
                    indices = cv2.dnn.NMSBoxes(nms_boxes, nms_confs, score_threshold=0.15, nms_threshold=self.iou)
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
