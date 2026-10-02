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
    def __init__(self, port=None, baudrate=115200, kp=0.08, servo_distance_mm=45.0):
        self.port = port
        self.baudrate = baudrate
        self.base_kp = kp
        self.servo_distance_mm = float(servo_distance_mm)
        self.kp = kp  # Computed dynamically from distance

        # Pan-Tilt Angles (0 - 180 deg, Center = 90)
        self.pan_angle = 90.0
        self.tilt_angle = 90.0
        self.pan_min = 10.0
        self.pan_max = 170.0
        self.tilt_min = 30.0
        self.tilt_max = 150.0
        self.parallax_deg = 0.0

        # Auto-compute limits and Kp based on servo separation distance
        self.recalculate_kinematics()

        # Calibration State
        self.is_calibrating = False
        self.calibration_progress = 0
        self.calibration_stage = "IDLE"
        self.calibration_stop_flag = False
        self.calibration_thread = None

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

    def recalculate_kinematics(self):
        """
        Dynamically adjusts proportional tracking gain and safe angular travel
        envelope as a function of physical inter-servo distance (baseline D).
        """
        d = max(10.0, min(200.0, self.servo_distance_mm))
        self.servo_distance_mm = d

        # Scale Kp inversely with sqrt of distance to normalize angular torque/lever arm
        nominal_d = 45.0
        scale = (nominal_d / d) ** 0.5
        self.kp = round(max(0.02, min(0.22, self.base_kp * scale)), 4)

        # Dual-servo clearance envelope auto-adjustment
        pan_margin = max(5.0, 10.0 + max(0.0, (d - 45.0) * 0.08))
        self.pan_min = round(pan_margin, 1)
        self.pan_max = round(180.0 - pan_margin, 1)

        tilt_margin = max(15.0, 42.0 - (d - 20.0) * 0.22)
        self.tilt_min = round(tilt_margin, 1)
        self.tilt_max = round(180.0 - tilt_margin, 1)

        # Baseline parallax angle at 1.2m nominal target distance
        import math
        self.parallax_deg = round(math.degrees(math.atan2(d, 1200.0)), 2)

    def set_servo_distance(self, distance_mm: float):
        """Update physical servo separation distance and automatically recalibrate kinematics."""
        with self.lock:
            self.servo_distance_mm = float(distance_mm)
            self.recalculate_kinematics()
            # Ensure current angles remain within new boundaries
            self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle))
            self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle))
        return self.get_state()

    def start_auto_calibration(self):
        """Initiate autonomous calibration movement sequence scaled to servo distance."""
        with self.lock:
            if self.is_calibrating:
                return False
            self.is_calibrating = True
            self.calibration_progress = 0
            self.calibration_stage = "INITIALIZING"
            self.calibration_stop_flag = False

        self.calibration_thread = threading.Thread(target=self._run_calibration_sequence, daemon=True)
        self.calibration_thread.start()
        return True

    def stop_auto_calibration(self):
        """Abort active calibration and return to neutral center."""
        self.calibration_stop_flag = True
        with self.lock:
            self.is_calibrating = False
            self.calibration_stage = "ABORTED"
            self.pan_angle = 90.0
            self.tilt_angle = 90.0
            self._set_laser(False)
            self.send_angles(90, 90)
        return self.get_state()

    def _run_calibration_sequence(self):
        """Execute smooth 5-stage automated calibration movement."""
        def interp_to(target_p, target_t, steps=25, delay=0.03):
            p_start, t_start = self.pan_angle, self.tilt_angle
            for step in range(1, steps + 1):
                if self.calibration_stop_flag:
                    return False
                frac = step / steps
                # Cosine smoothing (ease-in-out)
                smooth_frac = 0.5 * (1.0 - math.cos(math.pi * frac))
                cur_p = p_start + (target_p - p_start) * smooth_frac
                cur_t = t_start + (target_t - t_start) * smooth_frac
                with self.lock:
                    self.pan_angle = cur_p
                    self.tilt_angle = cur_t
                    self.send_angles(cur_p, cur_t)
                time.sleep(delay)
            return True

        import math
        try:
            # Stage 1: Neutralization (0 - 15%)
            with self.lock:
                self.calibration_stage = "NEUTRALIZING"
                self.calibration_progress = 10
            if not interp_to(90.0, 90.0, steps=20):
                return
            time.sleep(0.3)

            # Stage 2: Azimuth (Pan) Travel Calibration (15 - 45%)
            with self.lock:
                self.calibration_stage = f"PAN THROW SWEEP [{int(self.pan_min)}-{int(self.pan_max)}]"
                self.calibration_progress = 25
            if not interp_to(self.pan_min, 90.0, steps=30):
                return
            time.sleep(0.2)
            with self.lock:
                self.calibration_progress = 35
            if not interp_to(self.pan_max, 90.0, steps=40):
                return
            time.sleep(0.2)
            if not interp_to(90.0, 90.0, steps=30):
                return
            with self.lock:
                self.calibration_progress = 45

            # Stage 3: Elevation (Tilt) Travel Calibration (45 - 75%)
            with self.lock:
                self.calibration_stage = f"TILT THROW SWEEP [{int(self.tilt_min)}-{int(self.tilt_max)}]"
                self.calibration_progress = 55
            if not interp_to(90.0, self.tilt_min, steps=25):
                return
            time.sleep(0.2)
            with self.lock:
                self.calibration_progress = 65
            if not interp_to(90.0, self.tilt_max, steps=35):
                return
            time.sleep(0.2)
            if not interp_to(90.0, 90.0, steps=25):
                return
            with self.lock:
                self.calibration_progress = 75

            # Stage 4: 2-Servo Parallax Quadrant Verification (75 - 95%)
            with self.lock:
                self.calibration_stage = f"PARALLAX VERIFICATION [{self.servo_distance_mm}mm]"
                self.calibration_progress = 80
            p_offset = max(3.0, self.parallax_deg * 2.0)
            t_offset = max(3.0, self.parallax_deg * 2.0)

            quadrants = [
                (90.0 - p_offset, 90.0 - t_offset),
                (90.0 + p_offset, 90.0 - t_offset),
                (90.0 + p_offset, 90.0 + t_offset),
                (90.0 - p_offset, 90.0 + t_offset),
                (90.0, 90.0)
            ]
            for q_idx, (qp, qt) in enumerate(quadrants):
                if not interp_to(qp, qt, steps=15, delay=0.025):
                    return
                with self.lock:
                    self.calibration_progress = 80 + int((q_idx + 1) * 3)

            # Stage 5: Calibration Complete (100%)
            time.sleep(0.2)
            with self.lock:
                self.calibration_progress = 100
                self.calibration_stage = "CALIBRATION COMPLETE"
                self.is_calibrating = False
        except Exception:
            with self.lock:
                self.is_calibrating = False
                self.calibration_stage = "ERROR"

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
            # Suspend tracking while autonomous calibration is in progress
            if self.is_calibrating:
                return

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
            if self.is_calibrating:
                return
            self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle + d_pan))
            self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle + d_tilt))
            self.send_angles(self.pan_angle, self.tilt_angle)

    def center(self):
        """Reset servos to neutral center position (90, 90)."""
        with self.lock:
            if self.is_calibrating:
                self.stop_auto_calibration()
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
                "servo_distance_mm": self.servo_distance_mm,
                "kp": self.kp,
                "pan_limits": [self.pan_min, self.pan_max],
                "tilt_limits": [self.tilt_min, self.tilt_max],
                "parallax_deg": self.parallax_deg,
                "is_calibrating": self.is_calibrating,
                "calibration_progress": self.calibration_progress,
                "calibration_stage": self.calibration_stage,
                "laser_armed": self.laser_armed,
                "laser_firing": self.laser_firing,
                "is_simulated": self.is_simulated,
                "is_cooldown": time.time() < self.cooldown_until
            }
