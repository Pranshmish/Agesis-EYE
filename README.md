# Agesis EYE: Autonomous Pan-Tilt Target Tracking System

[![YOLOv8](https://img.shields.io/badge/YOLO-v8n-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![ONNX Runtime](https://img.shields.io/badge/ONNX-Runtime-blue.svg)](https://onnxruntime.ai/)
[![ESP32-CAM](https://img.shields.io/badge/Hardware-ESP32--CAM-red.svg)](https://www.espressif.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

**Agesis EYE** is an end-to-end autonomous vision and tracking system designed for rapid aerial target acquisition. An ESP32-CAM streams real-time video over Wi-Fi to a ground-station laptop, where an asynchronous zero-lag YOLO detection engine computes target coordinates and drives a 2-degree-of-freedom pan-tilt turret.

---

## 🏗️ System Architecture

```
┌─────────────────┐       Wi-Fi (MJPEG)       ┌──────────────────────────────┐
│  ESP32-CAM      │ ────────────────────────> │  Zero-Lag Stream Reader      │
│  (Stage 01)     │  320x240 @ 25-30 FPS      │  (Thread 1: requests buffer) │
└─────────────────┘                           └──────────────┬───────────────┘
                                                             │ Latest Frame
                                                             ▼
┌─────────────────┐       Coordinates         ┌──────────────────────────────┐
│  Pan-Tilt       │ <──────────────────────── │  Asynchronous YOLO Worker    │
│  Turret & Laser │    (dX, dY, Lock Signal)  │  (Thread 2: agesis06.onnx)   │
│  (Stage 05, 06) │                           └──────────────┬───────────────┘
└─────────────────┘                                          │
                                                             ▼
                                              ┌──────────────────────────────┐
                                              │  Real-Time 30+ FPS HUD       │
                                              │  (Main Thread: Reticle & UI) │
                                              └──────────────────────────────┘
```

---

## 📂 Repository Structure

Work through the pipeline folders in sequential order:

```
Agesis EYE/
├── 01 Camera Stream and Record/     # ESP32-CAM firmware, flasher, latency tests
├── 02 Dataset Collection and Labeling/ # Live capture and bounding box annotation tools
├── 03 Model Training/               # Detection architecture & training specifications
├── 04 Laptop Inference/             # High-performance zero-lag tracker & models
│   ├── models/
│   │   ├── agesis06.onnx            # Deployed ONNX model (45+ FPS CPU)
│   │   └── agesis06.pt              # Deployed PyTorch weights
│   ├── live_balloon_tracker.py      # Core decoupled tracking engine
│   ├── run_tracker_onnx.bat         # 1-Click student ONNX launcher
│   └── run_tracker_pt.bat           # 1-Click student PyTorch launcher
├── 05 Turret Control/               # 2-axis servo kinematics & closed-loop PID aiming
├── 06 Laser Safety/                 # Safety protocols, timeout interlocks & rules
├── run_live_tracker_onnx.bat        # Root 1-click ONNX launcher
└── run_live_tracker.bat             # Root 1-click PyTorch launcher
```

---

## ⚡ Workshop Student Quickstart

Workshop participants receive pre-compiled, optimized production models inside `04 Laptop Inference/models/` for immediate deployment:

### 1. Connect ESP32-CAM
1. Power the ESP32-CAM module via USB or 5V bench supply.
2. Ensure your laptop is connected to the same Wi-Fi network/hotspot as the ESP32.
3. Verify your camera stream URL in `01 Camera Stream and Record/camera_config.json`:
   ```json
   {
     "stream_url": "http://10.96.117.1:81/stream",
     "snapshot_url": "http://10.96.117.1/capture"
   }
   ```

### 2. Launch Tracker (1-Click)
Double-click **`run_live_tracker_onnx.bat`** (in project root) or **`04 Laptop Inference/run_tracker_onnx.bat`**.

- **Detection Speed**: 40–55+ FPS
- **Latency**: $\approx 18–25$ ms
- **Target Lock**: Multi-frame temporal confirmation eliminates false positives.

### 3. Interactive HUD Hotkeys

| Key | Function | Description |
| :---: | :--- | :--- |
| **`q`** / **`ESC`** | **Exit** | Gracefully disconnects stream and closes HUD |
| **`e`** | **Domain Transform** | Toggles Edge-Preserving CLAHE enhancement |
| **`+`** / **`=`** | **Conf +0.05** | Increases detection confidence threshold |
| **`-`** / **`_`** | **Conf -0.05** | Decreases confidence threshold |
| **`s`** | **Snapshot** | Saves an annotated debug screenshot |

---

## 🎯 Model Benchmark (agesis06)

Evaluated on held-out test splits using Edge-Preserving CLAHE (`EP-CLAHE`):

- **Recall**: **$91.6\%$** (Zero missed balloons within operating range)
- **Precision**: **$93.4\%$** (Zero false activations on human faces, hair, or dark shirts)
- **mAP@50**: **$0.879$**
- **Extreme FOV Handling**: Adaptive edge thresholds ensure continuous tracking across extreme left/right margins ($X_c < 0.18$ and $X_c > 0.82$).

---

## 🔒 Safety & Governance

1. **Hardware Interlock**: Laser remains disconnected or powered off during all tracking and calibration testing (Stage 01 through 05).
2. **Software Failsafe**: If detection drops for $>300$ ms, target lock is disengaged and turret actuation immediately ceases.
3. **Safety Review**: Read **`06 Laser Safety/06-laser-safety-rules.md`** before connecting any active emitter.
