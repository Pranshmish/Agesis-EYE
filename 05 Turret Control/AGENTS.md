# Stage 05: Aiming, Calibration & Turret Control Rules

## Rules & Constraints
1. **NO ARDUINO IDE**: Control, calibration, homography fitting, and protocol communication are managed entirely through Python scripts. Microcontroller firmware flashing is performed via `esptool` / Python CLI when needed.
2. **Electrical Isolation**: Drive servos with a separate 5-6V high-current power supply with common ground and decoupling capacitors.
3. **Dedicated Microcontroller**: Servos and laser control run on a dedicated MCU (ESP32 / UNO Q).
4. **Mechanical Safety Stops**: Use metal-gear servos (MG996R+) with physical stops restricting pan and tilt within the safe enclosure.
5. **Calibration Protocol**:
   - Perform 15-25 grid point calibration mapping (pan, tilt) to camera coordinates (x, y) using a low-power (< 1 mW) alignment laser or with laser off.
   - Fit 2nd-order polynomial or homography and store calibration matrix to disk.
6. **Closed-Loop Control**:
   - Use P/PI control on error between laser dot and target center.
   - Enforce 3-5 px deadband to prevent servo jitter. Rate-limit servo angular step speed.
7. **Communication Protocol**:
   - Format: `A,<pan>,<tilt>,<fire 0|1>`.
   - Firmware watchdog turns laser OFF if no command is received within 200 ms.
