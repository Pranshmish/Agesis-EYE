---
name: model-training
description: Train and honestly evaluate a YOLO detector for the black balloon, with accuracy targets and failure analysis
---

# Model Training

## Goal
A detector that is accurate on the real ESP32-CAM stream, evaluated on held-out sessions.

## Rules
1. Start with `yolov8n` or `yolo11n`. Move to `s` only if accuracy is insufficient and the laptop is fast enough.
2. Train at imgsz 640 (or match the camera resolution). Use pretrained COCO weights and fine-tune.
3. Train on Colab or Kaggle GPU if the laptop has no GPU.
4. Keep augmentation on (HSV, flip, scale, mosaic). Do not use vertical flip unless balloons truly appear upside down.
5. Judge by the held-out test split, not training metrics.
6. Report precision, recall, mAP50 and mAP50-95. For a laser, PRECISION matters most: a false positive means firing at the wrong thing.
7. Always inspect failure cases visually (confusion matrix and val predictions).

## Training
```bash
pip install ultralytics
yolo detect train data=dataset/data.yaml model=yolov8n.pt imgsz=640 epochs=100 batch=16 patience=25 project=runs name=balloon_v1
yolo detect val data=dataset/data.yaml model=runs/balloon_v1/weights/best.pt split=test
```

## Targets (starting goals)
- Precision at the chosen confidence threshold: 0.97 or higher
- Recall: 0.90 or higher
- Zero false positives on a pure-negative session (black objects, empty room)

## Improving accuracy (in order of impact)
1. More and better data from this camera in varied conditions.
2. Fix label errors.
3. Add hard negatives.
4. Hard-example retraining loop.
5. Larger model or higher imgsz.
6. Tune confidence threshold (choose it from the PR curve, then set it high for firing).

## Export
```bash
yolo export model=runs/balloon_v1/weights/best.pt format=onnx   # CPU-friendly
```
Keep every model version with a note on data and metrics in LOG.md.
