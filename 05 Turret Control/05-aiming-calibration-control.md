---
name: aiming-calibration-control
description: Map camera pixels to pan/tilt servo angles, calibrate, and close the loop using the laser dot position
---

# Aiming, Calibration and Control

## Goal
Servo angles that put the beam on the balloon center accurately and repeatably.

## Hardware rules
1. Mount camera and laser as close together and as parallel as possible to reduce parallax.
2. Drive servos from a separate 5-6V supply with enough current. Share GND with the controller.
3. Use a dedicated microcontroller (Arduino, ESP32 or UNO Q) for servos and the laser. The laptop sends commands over serial or WiFi.
4. Metal-gear servos (MG996R or better). Add a mechanical stop so the turret cannot point outside the safe zone.
5. Add a small capacitor across the servo supply and keep wiring short.

## Calibration (with laser OFF or a low-power red pointer only)
1. Move servos to 15-25 grid positions covering the working area.
2. At each, record (pan, tilt) and the pixel (x, y) where the dot appears in the camera.
3. Fit a mapping from (x, y) to (pan, tilt): start with a 2nd-order polynomial or homography. Check the error on points you did not use for fitting.
4. Save calibration to a file and re-run it whenever the camera or laser is moved.

## Closed-loop correction
1. Detect the laser dot (low-power mode) and the balloon center in the same frame.
2. Error = balloon_center minus dot. Convert to small angle steps and apply a P or PI controller. Limit the step size.
3. Add a deadband (about 3-5 px) so the servos do not jitter.
4. Smooth angle commands (exponential moving average) and rate-limit servo speed.

## Fire logic (all conditions must be true)
- Target locked for N frames (file 04).
- Aim error under threshold for M consecutive frames.
- Target angle inside the allowed safe zone.
- Dwell time: keep firing only while lock and aim hold. Stop immediately if any condition fails.
- Max continuous fire time (for example 2 s), then cooldown.

## Protocol (laptop to controller)
Simple text lines: `A,<pan>,<tilt>,<fire 0|1>`. The controller must turn the laser OFF if no valid command arrives within 200 ms.

## Done when
- With the laser off or low power, the dot lands within a few pixels of the balloon center across the whole workspace.
