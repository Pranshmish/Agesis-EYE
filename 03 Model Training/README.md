# Stage 03: Model Training & Architecture

Overview of the deep learning balloon detection architecture and pre-trained production models for the **Agesis EYE** autonomous tracking system.

---

## 🎓 Workshop Deliverable Notice

For this workshop, the deep learning model has already been trained, validated, and optimized for you:

- **Pre-trained Production Models**: Pre-installed in **`04 Laptop Inference/models/`**
  - `agesis06.onnx` (High-Performance ONNX Runtime, 45+ FPS)
  - `agesis06.pt` (PyTorch YOLOv8n Weights)
- **Status**: Ready for immediate deployment.
- **Action**: Students can proceed directly to **Stage 04: Laptop Inference** to run live real-time detection on the ESP32-CAM stream.

> **Privacy & Access Boundary**: Raw training telemetry datasets, domain adaptation generators, and cloud GPU cluster training credentials are restricted to the workshop teaching staff and are maintained in private instructor repositories.

---

## 🧠 Model Architecture & Specifications

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | Ultralytics YOLOv8 Nano (`yolov8n`) |
| **Input Resolution** | $384 \times 384$ RGB |
| **Inference Precision** | FP32 CPU Optimized / Dynamic INT8 compatible |
| **Target Class** | `0: balloon` (Specially calibrated for black aerial targets) |
| **Domain Transformation** | Edge-Preserving CLAHE (`EP-CLAHE`) domain adaptation |
| **Recall Rate** | **$91.6\%$** on unseen flight verification splits |
| **Precision Rate** | **$93.4\%$** with zero false triggers on human faces/hair |
| **mAP@50** | **$0.879$** |
| **Target Latency** | $<25$ ms on modern laptop CPU |

---

## 🎯 Extreme FOV Edge Tracking & Spatial Calibration

During real-time deployment, targets moving to the extreme left or extreme right margins of the camera field of view experience lens distortion and partial boundary clipping.

The deployed tracker implements:
1. **Adaptive Edge Confidence Thresholding**: Dynamically adapts from $0.35$ in the central optical zone to $0.20$ when $X_c < 0.18$ or $X_c > 0.82$.
2. **Aspect Ratio Tolerance**: Expands bounding box aspect ratio filtering ($0.55 \le \frac{w}{h} \le 1.70$) to prevent missed detections on wide-angle barrel edges.
3. **Temporal Multi-Frame Confirmation**: Requires consecutive locked frames to eliminate transient background noise before issuing actuation commands.
