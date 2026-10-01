# Agesis EYE: Laser Balloon Turret Rules & Guidelines

Project: 2-servo pan-tilt turret. An ESP32-CAM streams video to a laptop, a locally run model detects a black balloon, and a laser pops it.

## Global Rules & Constraints
1. **Sequential Progression**: Work through files and pipeline phases in order:
   - `01-esp32cam-stream-and-record`
   - `02-dataset-collection-and-labeling`
   - `03-model-training`
   - `04-laptop-inference`
   - `05-aiming-calibration-control`
   - `06-laser-safety-rules`
   Do not skip steps; each depends directly on the previous.
2. **Camera Consistency**: Collect dataset frames with the exact same ESP32-CAM, mounting orientation, and resolution (VGA/SVGA) as deployment.
3. **Laser Defaults OFF**: The laser must remain powered off or physically disconnected during development and testing until all calibration and verification checks pass.
4. **Safety Gating**:
   - Wear rated laser safety goggles.
   - Employ non-reflective matte backstops.
   - Hardware pull-down resistor on laser control pin and 200ms watchdog shutdown.
   - High confidence threshold (>= 0.70) and multi-frame lock before arming.
   - Emergency kill switch and rate/angle limits enforced at all times.
