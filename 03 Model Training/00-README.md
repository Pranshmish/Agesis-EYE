# Laser Balloon Turret: Skills and Rules Index

Project: 2-servo pan-tilt turret. An ESP32-CAM streams video to a laptop, a locally run model detects a black balloon, and a laser pops it.

Work through the files in order. Do not skip ahead: each stage depends on the previous one.

| # | File | Goal |
|---|------|------|
| 01 | esp32cam-stream-and-record | Stable stream and raw video recording |
| 02 | dataset-collection-and-labeling | Frames, labels, splits |
| 03 | model-training | Train YOLO, evaluate honestly |
| 04 | laptop-inference | Real-time detection and tracking |
| 05 | aiming-calibration-control | Pixel to servo angle mapping, closed loop |
| 06 | laser-safety-rules | Hard rules. Read before powering any laser |

## Global rules
- Collect data with the SAME camera, resolution and mounting used in deployment.
- Change one thing at a time and log it (a plain `LOG.md` is enough).
- Laser stays OFF by default. Every stage before 06 is tested with the laser disconnected or replaced by a low-power red pointer.
