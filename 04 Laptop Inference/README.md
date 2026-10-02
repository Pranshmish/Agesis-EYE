# Stage 04: Real-Time Laptop Inference & HUD Tracking

Production-grade real-time detection, HUD telemetry, and targeting reticle for the **Agesis EYE** autonomous balloon tracking system.

---

## ⚡ Quickstart (Workshop Students)

You can launch the live tracker with a single click using the pre-configured Windows batch launchers:

### Option A: Ultra-Fast ONNX Runtime (Recommended)
Double-click **`run_tracker_onnx.bat`** (or from the project root: `run_live_tracker_onnx.bat`).
- **Engine**: ONNX Runtime (CPU multi-threaded, SIMD AVX2 acceleration)
- **Speed**: **40–55+ FPS** on standard laptop CPUs
- **Latency**: $\approx 18–25$ ms per frame

### Option B: PyTorch YOLOv8n
Double-click **`run_tracker_pt.bat`** (or from the project root: `run_live_tracker.bat`).
- **Engine**: PyTorch (`ultralytics.YOLO`)
- **Speed**: **25–35 FPS**

---

## 📦 Model Weights (`models/`)

The pre-trained production model weights are located directly in this folder under `models/`:

| File | Format | Resolution | Description |
| :--- | :--- | :--- | :--- |
| **`models/agesis06.onnx`** | ONNX Runtime | $384 \times 384$ | Highly optimized for real-time CPU deployment |
| **`models/agesis06.pt`** | PyTorch YOLOv8n | $384 \times 384$ | Native PyTorch weights |

> **Note**: Both models were trained on 100 epochs with EP-CLAHE domain adaptation, achieving **91.6% Recall** and **93.4% Precision** with extreme-edge FOV calibration.

---

## 🎮 Live HUD Keyboard Controls

While the live camera tracking window is focused, you can use the following interactive hotkeys:

| Key | Action | Description |
| :---: | :--- | :--- |
| **`q`** / **`ESC`** | **Exit Tracker** | Safely shuts down the stream reader and releases threads |
| **`e`** | **Toggle EP-CLAHE** | Switches edge-preserving CLAHE domain enhancement ON/OFF |
| **`+`** / **`=`** | **Conf +0.05** | Increases the detection confidence threshold (higher precision) |
| **`-`** / **`_`** | **Conf -0.05** | Decreases threshold (higher sensitivity for faint targets) |
| **`s`** | **Snapshot** | Saves annotated frame to `scratch/` for verification |

---

## 🖥️ Command-Line Usage

You can also run the tracker directly using Python:

```powershell
# Default launch (automatically finds models/agesis06.onnx and camera_config.json):
python "04 Laptop Inference/live_balloon_tracker.py"

# Specify a custom stream URL or local webcam:
python "04 Laptop Inference/live_balloon_tracker.py" --source "http://10.96.117.1:81/stream"
python "04 Laptop Inference/live_balloon_tracker.py" --source 0  # Webcam

# Run with custom confidence threshold:
python "04 Laptop Inference/live_balloon_tracker.py" --conf 0.40 --imgsz 384
```

---

## 🎯 Targeting & Telemetry HUD Elements

- **Aiming Reticle (Crosshair)**: Indicates the optical center of the camera view.
- **Bounding Box & Target Lock**:
  - 🟠 **Orange Box (`ACQUIRING`)**: Target detected but waiting for consecutive frame confirmation.
  - 🟢 **Green Box (`LOCKED`)**: Stable target lock confirmed across multiple frames. Target is safe to track.
- **Error Vector ($\Delta X, \Delta Y$)**: Pixel offset from the camera optical center to the target center:
  - $\Delta X = X_{\text{target}} - X_{\text{center}}$
  - $\Delta Y = Y_{\text{target}} - Y_{\text{center}}$
- **Extreme FOV Edge Guides**: Vertical dashed guides calibrate detection when the target approaches the extreme peripheral margins (`[EXTREME LEFT]` / `[EXTREME RIGHT]`).
