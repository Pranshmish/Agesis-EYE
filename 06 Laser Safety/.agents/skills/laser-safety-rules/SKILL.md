---
name: laser-safety-rules
description: Hard safety rules and protocols for the laser stage of the balloon turret. Must be satisfied before powering any laser.
---

# Laser Safety Rules (mandatory)

A laser strong enough to pop a black balloon can cause permanent eye damage, including from reflections, and can start fires or burn skin. Treat it as a hazardous device.

## Before powering the laser
1. Wear laser safety goggles rated for YOUR laser wavelength and power, every time the system is powered.
2. Build or use an enclosure or backstop (non-reflective, non-flammable, for example matte black metal or acrylic shield) behind the balloon area.
3. Remove reflective objects (mirrors, glass, shiny metal) from the beam path.
4. Keep people and animals out of the room while firing.

## Hardware safeguards
- Laser power runs through its own physical kill switch.
- Laser driver defaults OFF (pull-down resistor on the control pin).
- Controller watchdog: no valid command within 200 ms means laser OFF.
- Mechanical limits on pan and tilt so the beam cannot sweep outside the safe zone (for example only downward into the backstop).
- Optional: key switch or arming button that must be held or enabled to allow firing.

## Software safeguards
- Fire only if: target locked, aim error small, target inside the safe zone, continuous fire under the limit.
- Crash, disconnect or exception: send laser OFF.
- Log every fire event with time and confidence.
- Never fire on detections below the high confidence threshold. Precision beats recall.

## Testing order
1. Whole pipeline with the laser disconnected.
2. Low-power red pointer (Class 2, under 1 mW) for calibration and aim tests.
3. Higher power only after all above are stable, and only inside the enclosure with goggles on.

## Legal and practical
- Check your local rules on laser power limits.
- Never aim at people, vehicles, windows or open areas.
- If anything behaves unexpectedly, cut power first, debug later.
