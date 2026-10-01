# Laser Balloon Turret Rules & Engineering Guidelines

Project: 2-servo pan-tilt turret. An ESP32-CAM streams video to a laptop, a locally run model detects a black balloon, and a laser pops it.

## Mandatory Workflow & Progression
Work through the project stages strictly in order. Do not skip ahead; each stage depends on the previous one:
1. `01-esp32cam-stream-and-record`: Stable stream and raw video recording.
2. `02-dataset-collection-and-labeling`: Extraction, annotation, and session-based splits.
3. `03-model-training`: YOLO training, evaluation on held-out test splits, false-positive elimination.
4. `04-laptop-inference`: Real-time low-latency stream processing, multi-frame target locking.
5. `05-aiming-calibration-control`: Pixel-to-servo angle calibration, closed-loop feedback, deadband, rate-limiting.
6. `06-laser-safety-rules`: Hard physical, hardware, and software safety gates.

## Global Rules
- **Camera Consistency**: Always collect data with the EXACT same camera, resolution, and mounting used in physical deployment. Different camera heights or angles shift data distribution.
- **Controlled Changes**: Change only one variable at a time and document it in `LOG.md`.
- **Default Laser State**: The laser must remain completely OFF and disconnected by default. All stages prior to Stage 06 must be developed and tested with the laser disconnected or replaced by a harmless low-power red pointer (< 1 mW).
- **Precision Over Recall**: For laser firing, false positives are unacceptable. Confidence thresholds must be set conservatively high (>= 0.70) with multi-frame confirmation.
