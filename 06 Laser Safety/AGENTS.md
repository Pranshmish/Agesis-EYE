# Stage 06: Laser Safety Rules & Compliance

## Mandatory Safety Rules
1. **Eye Protection**: Certified laser safety goggles matched to operational wavelength and optical power rating must be worn whenever laser circuits are powered.
2. **Backstop & Enclosure**: Target area must have a non-reflective, flame-resistant backstop (matte black metal plate or acrylic shield).
3. **Specular Reflection Hazard**: Clear all mirrors, glass, reflective plastics, and shiny metal surfaces from the room.
4. **Exclusion Zone**: Keep all people and pets out of the room during active laser testing.
5. **Hardware Protections**:
   - Mechanical inline kill switch.
   - Laser control pin pulled down to GND so driver defaults to OFF.
   - 200 ms controller watchdog timer.
   - Physical mechanical stops on turret axes.
6. **Software Firing Gates**:
   - Only fire when target locked >= 5 frames AND aim error within deadband threshold.
   - Hard maximum continuous firing limit (<= 2 seconds) with forced thermal cooldown.
   - Any disconnect, lag spike (> 300 ms), or exception commands laser OFF immediately.
