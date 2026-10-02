# Agesis EYE: Autonomous Vision & Targeting Ground Station

[![ONNX Runtime](https://img.shields.io/badge/AI_Engine-ONNX_Runtime_(45+_FPS)-cyan.svg)](https://onnxruntime.ai/)
[![ESP32-CAM](https://img.shields.io/badge/Transmitter-ESP32--CAM-red.svg)](https://www.espressif.com/)
[![Web Ground Station](https://img.shields.io/badge/Interface-FastAPI_+_Vanilla_JS_HUD-green.svg)](http://127.0.0.1:8000)

**Agesis EYE** is an autonomous tracking and targeting ground station for a 2-axis Pan-Tilt turret. An ESP32-CAM streams live video over Wi-Fi, and a ground-station AI engine detects aerial targets with zero latency and drives the turret in closed-loop servo tracking.

---

## ⚡ 3-Step Workshop Quickstart

### 1. Flash the Camera (ESP32-CAM)
1. Open **`firmware/esp32_cam_stream/esp32_cam_stream.ino`** in the Arduino IDE.
2. Enter your Wi-Fi hotspot SSID and password.
3. Select board `AI Thinker ESP32-CAM` and upload the sketch.
4. Note the camera stream IP displayed in the Serial Monitor (e.g. `http://10.96.117.1:81/stream`).

### 2. Launch the Ground Station (1-Click)
Double-click **`run.bat`** in the project root folder.
- Starts the high-performance AI inference backend.
- Automatically loads the optimized model **`agesis06.onnx`**.
- Opens your browser to **`http://127.0.0.1:8000`** with the tactical HUD.

### 3. Track and Target
- Point the camera at a balloon to watch the AI acquire target lock!
- View real-time telemetry ($\Delta X, \Delta Y$ pixel offsets, confidence %, tracking latency).
- Use the on-screen D-Pad or connect your 2-axis pan/tilt servos.

---

## 📁 Repository Structure

Designed to be simple, clean, and beginner-friendly:

```
Agesis EYE/
├── frontend/                   # Tactical HUD web interface
│   ├── index.html              # Ground station layout & gauges
│   ├── style.css               # Cyberpunk dark mode & glassmorphism
│   └── app.js                  # Real-time WebSocket & controls
├── backend/                    # Python AI inference & control server
│   ├── models/                 # Pre-packaged production models
│   │   ├── agesis06.onnx       # High-speed ONNX model (45+ FPS CPU)
│   │   └── agesis06.pt         # Native PyTorch YOLOv8n weights
│   ├── app.py                  # FastAPI web server
│   ├── tracker.py              # Zero-lag stream reader & YOLO engine
│   ├── turret.py               # Closed-loop PID servo aiming & safety
│   └── camera_config.json      # Camera stream IP settings
├── firmware/                   # ESP32-CAM transmitter code
│   ├── esp32_cam_stream/       # Arduino IDE streaming sketch
│   ├── flash_camera.py         # Optional command-line flasher
│   └── serial_monitor.py       # Serial monitor utility
├── run.bat                     # 1-Click launcher
├── README.md                   # Beginner guide
└── .gitignore                  # Keeps private training assets secure
```

---

## 🎮 Tactical HUD Interactive Controls

| Control | Action | Description |
| :---: | :--- | :--- |
| **📷 SNAPSHOT** | Capture Frame | Saves an annotated debug screenshot with bounding boxes |
| **✨ EP-CLAHE** | Domain Transform | Enhances contrast for faint or dark balloons |
| **🎯 CONFIDENCE SLIDER** | Adjust Sensitivity | Tune detection threshold between $10\%$ and $90\%$ (Default: $0.35$) |
| **🚨 LASER EMITTER** | Safety Master Switch | Toggle between **SAFE (DISARMED)** and **ARMED (READY)** |
| **🕹️ D-PAD JOG** | Servo Jog Test | Nudges Pan/Tilt servos in $5^\circ$ increments |
| **🔍 AUTO-DISCOVER** | Network Scan | Automatically detects your ESP32-CAM IP on port 81 |

---

## 🔒 Safety Interlocks

1. **Safety Cutoff**: The laser emitter will **never** fire unless the AI has confirmed a stable target lock for $\ge 3$ consecutive frames.
2. **Auto-Disarm**: If target lock is broken or the stream drops for $>300$ ms, the laser is shut off immediately.
3. **Continuous Fire Timeout**: Firing duration is hardware-limited to a maximum of $1.5$ seconds with a mandatory cooling period.
4. **Eyewear**: Never look directly into an active laser beam; ensure certified laser safety goggles are worn when operating with an emitter connected.
