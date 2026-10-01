---
name: laptop-inference
description: Real-time local detection and tracking of the balloon from the ESP32-CAM stream on a laptop.
---

# Laptop Inference and Tracking

## Goal
Low-latency detection from the live stream, with a stable target (cx, cy) and a confidence-gated "target locked" signal.

## Rules
1. Read frames in a separate thread and always run inference on the LATEST frame. Old buffered frames cause laggy aiming.
2. Use the same resolution as training.
3. Use a high confidence threshold for firing decisions (start at 0.7 or higher).
4. Require N consecutive confirmed frames (for example 5) before the target counts as locked. One-frame detections are never trusted.
5. Track the target (ByteTrack via Ultralytics, or a simple Kalman filter) to smooth the center point.
6. If the stream drops or no detection arrives for 300 ms, send "no target" and the laser must go OFF.
7. Log FPS and end-to-end latency. Target 15+ FPS and under 150 ms total.

## Skeleton
```python
import cv2, threading, time
from ultralytics import YOLO

URL = "http://ESP_IP:81/stream"
model = YOLO("runs/balloon_v1/weights/best.pt")
latest = {"frame": None}

def reader():
    cap = cv2.VideoCapture(URL)
    while True:
        ok, f = cap.read()
        if ok: latest["frame"] = f
threading.Thread(target=reader, daemon=True).start()

CONF, LOCK_N, streak = 0.7, 5, 0
while True:
    f = latest["frame"]
    if f is None: continue
    r = model.track(f, conf=CONF, persist=True, verbose=False)[0]
    if len(r.boxes):
        b = max(r.boxes, key=lambda b: float(b.conf))
        x1, y1, x2, y2 = map(float, b.xyxy[0])
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        streak += 1
        locked = streak >= LOCK_N
    else:
        streak, locked = 0, False
    # send (cx, cy, locked) to aiming controller (file 05)
    cv2.imshow("det", r.plot())
    if cv2.waitKey(1) == 27: break
```

## Done when
- Detection is smooth and stable on a live stream, with correct no-target behavior when the balloon leaves view.
