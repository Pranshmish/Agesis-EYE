"""
Agesis EYE - Pan-Tilt Turret Controller & Laser Safety Interlock
Handles closed-loop aiming servo kinematics and strict laser safety protocols.
"""

import time
import threading

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class TurretController:
    """Manages pan-tilt servo tracking and laser safety interlock protocols."""
    def __init__(self, port=None, baudrate=115200, kp=0.08):
        self.port = port
        self.baudrate = baudrate
        self.kp = kp  # Proportional tracking gain

        # Pan-Tilt Angles (0 - 180 deg, Center = 90)
        self.pan_angle = 90.0
        self.tilt_angle = 90.0
        self.pan_min, self.pan_max = 10.0, 170.0
        self.tilt_min, self.tilt_max = 30.0, 150.0

        # Laser Safety State
        self.laser_armed = False
        self.laser_firing = False
        self.fire_start_time = 0.0
        self.max_continuous_fire_sec = 1.5
        self.cooldown_until = 0.0
        self.cooldown_sec = 2.0
        self.last_target_time = 0.0

        # Serial Connection
        self.serial_conn = None
        self.is_simulated = True
        self.lock = threading.Lock()

        self._connect_serial()

    def _connect_serial(self):
        if not HAS_SERIAL or not self.port:
            self.is_simulated = True
            return

        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(1.0)
            self.is_simulated = False
            self.send_angles(90, 90)
        except Exception:
            self.is_simulated = True
            self.serial_conn = None

    def update_aiming(self, dx, dy, locked):
        """Update pan/tilt angles based on optical pixel error (closed-loop)."""
        now = time.time()
        with self.lock:
            if locked and abs(dx) > 3 or abs(dy) > 3:
                # Delta X adjusts Pan, Delta Y adjusts Tilt
                self.pan_angle += -dx * self.kp
                self.tilt_angle += dy * self.kp

                self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle))
                self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle))

                self.last_target_time = now
                self.send_angles(self.pan_angle, self.tilt_angle)

            # Laser Safety State Machine
            if not self.laser_armed:
                self._set_laser(False)
            elif not locked or (now - self.last_target_time > 0.3):
                # Automatic Cutoff: Target lock lost for >300ms
                self._set_laser(False)
            elif now < self.cooldown_until:
                # Cooling down after maximum fire duration
                self._set_laser(False)
            elif locked and abs(dx) < 15 and abs(dy) < 15:
                # On target: Firing allowed up to max continuous duration
                if not self.laser_firing:
                    self.fire_start_time = now
                    self._set_laser(True)
                elif now - self.fire_start_time > self.max_continuous_fire_sec:
                    # Exceeded max fire time -> force cooldown
                    self._set_laser(False)
                    self.cooldown_until = now + self.cooldown_sec
            else:
                self._set_laser(False)

    def nudge(self, d_pan, d_tilt):
        """Manual jog for servo calibration testing."""
        with self.lock:
            self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle + d_pan))
            self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle + d_tilt))
            self.send_angles(self.pan_angle, self.tilt_angle)

    def center(self):
        """Reset servos to neutral center position (90, 90)."""
        with self.lock:
            self.pan_angle = 90.0
            self.tilt_angle = 90.0
            self._set_laser(False)
            self.send_angles(90, 90)

    def set_armed(self, armed: bool):
        with self.lock:
            self.laser_armed = armed
            if not armed:
                self._set_laser(False)

    def _set_laser(self, on: bool):
        self.laser_firing = on
        if self.serial_conn and self.serial_conn.is_open:
            cmd = f"L{1 if on else 0}\n"
            try:
                self.serial_conn.write(cmd.encode("ascii"))
            except Exception:
                pass

    def send_angles(self, pan, tilt):
        if self.serial_conn and self.serial_conn.is_open:
            cmd = f"P{int(pan)} T{int(tilt)}\n"
            try:
                self.serial_conn.write(cmd.encode("ascii"))
            except Exception:
                pass

    def get_state(self):
        with self.lock:
            return {
                "pan": round(self.pan_angle, 1),
                "tilt": round(self.tilt_angle, 1),
                "laser_armed": self.laser_armed,
                "laser_firing": self.laser_firing,
                "is_simulated": self.is_simulated,
                "is_cooldown": time.time() < self.cooldown_until
            }
