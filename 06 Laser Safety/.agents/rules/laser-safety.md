# Laser Safety Rules (Mandatory System Constraints)

A laser capable of popping balloons presents extreme risks of permanent ocular damage (including from specular reflections), skin burns, and fire hazards. Treat it as a hazardous industrial device.

## 1. Physical Environment Rules
- **Eye Protection**: Laser safety goggles certified for the specific operational wavelength and optical power rating MUST be worn whenever the system is powered.
- **Backstop & Enclosure**: An enclosure or non-reflective, non-flammable backstop (e.g. matte black metal plate or acrylic shield) must back the entire target zone.
- **Reflection Elimination**: Mirrors, glass, polished surfaces, and shiny metals must be removed entirely from the line of fire.
- **Exclusion Zone**: No people or animals may enter the firing zone during active power.

## 2. Hardware Safeguards
- **Physical Kill Switch**: Independent mechanical emergency shutoff in line with the laser power supply.
- **Failsafe Default**: Pull-down resistor on the laser driver gate/control pin so it remains OFF if undriven or during microcontroller reboot.
- **Microcontroller Watchdog**: The firmware must automatically cut laser power if no keep-alive/aiming command is received within 200 ms.
- **Mechanical Stops**: Hardware physical stops on pan/tilt axes preventing the beam from traversing outside designated safe coordinates.

## 3. Software Safeguards & Firing Gate
Laser firing (`fire=1`) is strictly forbidden unless ALL conditions evaluate to TRUE simultaneously:
1. Multi-frame target lock confirmed (e.g. >= 5 consecutive frames).
2. Angular aim error is strictly below tolerance for M consecutive frames.
3. Coordinates are within the verified safe zone bounds.
4. Continuous fire dwell time is under the hard limit (e.g., maximum 2 seconds), followed by forced cooldown.
5. On any exception, crash, or frame drop (>300 ms without frame/detection), immediately signal `fire=0`.

## 4. Staged Testing Protocol
1. Test software and servos with laser completely disconnected.
2. Calibrate and test aiming using only a Class 2 (< 1 mW) low-power alignment pointer.
3. High-power laser integration is only permitted after all software, hardware, and physical barriers are fully validated.
