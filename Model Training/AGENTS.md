# Stage 03: Model Training Rules

## Rules & Constraints
1. **Model Selection**: Start with `yolov8n` or `yolo11n`. Fine-tune from pretrained weights. Only scale up if necessary and laptop compute allows.
2. **Resolution Alignment**: Match `imgsz` (640 or camera SVGA resolution) directly to camera capture settings.
3. **Augmentations**: Use HSV shifts, horizontal flip, scaling, and mosaic. Avoid vertical flip unless upside-down balloons are expected.
4. **Evaluation Standard**:
   - Evaluate solely on the held-out test split, never on train metrics.
   - Prioritize Precision (target >= 0.97) over Recall (target >= 0.90) to prevent false fires.
   - Zero false positives on pure negative test sets.
5. **Model Registry & Tracking**:
   - Save every trained model version and record metrics in `LOG.md`.
   - Export best checkpoints to ONNX format for efficient CPU/laptop inference.
