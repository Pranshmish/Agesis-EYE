# Stage 02: Dataset Collection & Labeling

Tools and automated scripts to create a clean, leak-free YOLO dataset for the **Agesis EYE** autonomous balloon detection and tracking system.

---

## 📁 Pipeline Overview

```
                      [ ESP32-CAM Stream ]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
    collect_live.py                       Stage 01 Videos
  (live capture via SPACE/auto)          (record_stream.py)
            │                                     │
            │                                     ▼
            │                             extract_frames.py
            │                            (extract 1-2 FPS)
            └──────────────────┬──────────────────┘
                               ▼
                       raw_frames/<session>/
                               │
                               ▼
                        label_helper.py
                    (bounding box annotation)
                               │
                               ▼
                      organize_dataset.py
                (split by session, no leakage)
                               │
                               ▼
                            dataset/
                      ├── images/ (train, val, test)
                      ├── labels/ (train, val, test)
                      └── data.yaml
```

---

## 🛠️ Scripts & Usage

### 1. Live Frame Collection (`collect_live.py`)
Stream live from the ESP32-CAM (uses settings in `camera_config.json` automatically):
```bash
# Manual capture session (press SPACE to capture frame)
python collect_live.py --session daylight_near

# Auto-capture every 0.7 seconds (1.4 FPS)
python collect_live.py --session flight_tracking --auto 0.7

# Capture background / negative frames (no balloon)
python collect_live.py --session room_empty --negative --auto 1.0
```
**Keyboard Controls:**
- `SPACE`: Capture single frame
- `N`: Toggle negative mode (saves empty label file)
- `A`: Toggle auto-capture on/off
- `+/-`: Adjust auto-capture interval
- `Q` or `ESC`: Exit and save session summary

---

### 2. Extract Frames from Recorded Videos (`extract_frames.py`)
Extract low-framerate images (avoiding near-duplicates) from `.avi` videos:
```bash
# Process all videos from Stage 01 raw_video/
python extract_frames.py

# Extract from a specific video at 1 frame per second
python extract_frames.py --video "../01 Camera Stream and Record/raw_video/session.avi" --interval 1.0
```

---

### 3. Automatic Bounding Box Labeler (`auto_label.py`)
Automatically detects the balloon and tracks it across all session frames:
```bash
# Auto-label frames in session_01
python auto_label.py --dir raw_frames/session_01

# Run with visual inspection window
python auto_label.py --dir raw_frames/session_01 --show
```
- Uses circle contour geometry and specular darkness analysis to locate the balloon.
- Writes standard YOLO `.txt` annotations for all frames automatically.
- Automatically marks frames as negative (empty file) if the balloon is occluded or absent.
- Generates `auto_label_preview.jpg` (a 3x3 sample grid) for instant verification.

---

### 4. Manual Labeling Tool (`label_helper.py`)
Lightweight, offline OpenCV tool if you wish to adjust or manually inspect boxes:
```bash
# Label or review extracted frames
python label_helper.py --dir raw_frames/session_01
```
**Controls:**
- **Mouse Drag**: Draw box around balloon
- `S` or `SPACE`: Save annotation and move to next image
- `A`: Go back to previous image
- `C`: Clear current box
- `X`: Mark as negative (saves empty label)
- `Q` or `ESC`: Quit

---

### 5. Organize YOLO Dataset (`organize_dataset.py`)
Splits frames **strictly by session** (no frame leakage between splits) and creates `data.yaml`:
```bash
# Auto-split (~70% train, ~20% val, ~10% test by session)
python organize_dataset.py --auto

# Explicit session split
python organize_dataset.py --train s1,s2,s3 --val s4 --test s5
```

---

## 📐 Dataset Rules
1. **Target**: 500+ positive images, 15-25% hard negatives (empty labels).
2. **Session Leakage Prevention**: Never mix frames of the same flight/session between train and val/test.
3. **Class**: Single class `0: balloon`.
