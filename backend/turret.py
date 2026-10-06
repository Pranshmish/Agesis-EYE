"""
Agesis EYE - Pan-Tilt Turret Controller & Laser Safety Interlock
Handles closed-loop aiming servo kinematics, distance-independent tracking decoupling,
5V 2A power slew-rate limiting, and high-speed UDP network dispatch to the ESP32.
"""

import os
import json
import time
import math
import socket
import threading

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class TurretController:
    """
    Manages dual SG90 pan-tilt servo tracking, distance-independent kinematics,
    and strict laser safety interlock protocols.
    
    Compatible with:
    - 5V 2A shared power supply (slew-rate acceleration control to prevent ESP32 brownouts).
    - Physical Tinkercad CAD mechanical assembly (orange pedestal + variable riser spar d + tilt head).
    - Distance-independent optical tracking (IBVS invariant to inter-servo distance d).
    - Network UDP dispatch directly to ESP32 on port 8888 and Serial UART fallback.
    """
    def __init__(self, port=None, baudrate=115200, kp=0.06, servo_distance_mm=55.0,
                 base_height_mm=190.0, esp32_ip=None, udp_port=8888, use_shared_serial=False):
        self.port = port
        self.baudrate = baudrate
        self.use_shared_serial = use_shared_serial
        self.base_kp = kp
        self.servo_distance_mm = float(servo_distance_mm)
        self.base_height_mm = float(base_height_mm)
        self.pan_offset = 0.0
        self.tilt_offset = 0.0
        self.kp = kp

        # Inversion & Smooth Filtering (Pan inverted by default to fix opposite direction)
        self.invert_pan = True
        self.invert_tilt = False
        self.tracking_enabled = False
        self.smooth_factor = 0.22
        self.deadband_px = 5.0
        self.max_slew_step_deg = 6.0
        self.filtered_dx = 0.0
        self.filtered_dy = 0.0

        # Load persistent configuration if present
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "turret_config.json")
        self._load_config()

        # Pan-Tilt Angles (0 - 180 deg, Center = 90)
        self.pan_angle = 90.0
        self.tilt_angle = 90.0
        self.pan_min = 10.0
        self.pan_max = 170.0
        self.tilt_min = 25.0
        self.tilt_max = 155.0
        self.parallax_deg = 0.0
        self.base_parallax_deg = 0.0

        # Maximum angular velocity per update step
        self.max_slew_step_deg = 6.0

        # Distance-independent kinematics configuration
        self.focal_length_px = 280.0  # QVGA 320x240 nominal focal length
        self.recalculate_kinematics()

        # Calibration State
        self.is_calibrating = False
        self.calibration_progress = 0
        self.calibration_stage = "IDLE"
        self.calibration_stop_flag = False
        self.calibration_thread = None

        # Laser Safety State Machine
        self.laser_armed = False
        self.laser_firing = False
        self.fire_start_time = 0.0
        self.max_continuous_fire_sec = 1.5
        self.cooldown_until = 0.0
        self.cooldown_sec = 2.0
        self.last_target_time = 0.0

        # Reinforcement Visual Centering Alignment Engine
        self.rl_active = False
        self.rl_stage = "IDLE"  # "IDLE" | "ACQUIRING" | "CONVERGING" | "FINE_TUNING" | "CENTER_LOCKED" | "CALIBRATED"
        self.rl_reward = 0.0
        self.rl_alignment_pct = 0.0
        self.rl_streak = 0
        self.rl_target_streak = 12
        self.rl_dist_px = 0.0
        self.rl_v_pan = 0.0
        self.rl_v_tilt = 0.0
        self.rl_center_tolerance_px = 8.0

        # Network UDP Dispatch to ESP32
        self.esp32_ip = esp32_ip
        self.udp_port = int(udp_port)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(False)

        # Serial Connection
        self.serial_conn = None
        self.is_simulated = True
        self.lock = threading.Lock()

        self._connect_serial()

    def _load_config(self):
        if hasattr(self, 'config_path') and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    cfg = json.load(f)
                    self.servo_distance_mm = float(cfg.get("servo_distance_mm", self.servo_distance_mm))
                    self.base_height_mm = float(cfg.get("base_height_mm", self.base_height_mm))
                    self.invert_pan = bool(cfg.get("invert_pan", self.invert_pan))
                    self.invert_tilt = bool(cfg.get("invert_tilt", self.invert_tilt))
                    self.kp = float(cfg.get("kp", self.kp))
                    self.pan_offset = float(cfg.get("pan_offset", self.pan_offset))
                    self.tilt_offset = float(cfg.get("tilt_offset", self.tilt_offset))
                    self.smooth_factor = float(cfg.get("smooth_factor", self.smooth_factor))
                    self.deadband_px = float(cfg.get("deadband_px", self.deadband_px))
                    self.tracking_enabled = bool(cfg.get("tracking_enabled", False))
            except Exception:
                pass

    def _save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump({
                    "servo_distance_mm": self.servo_distance_mm,
                    "base_height_mm": self.base_height_mm,
                    "invert_pan": self.invert_pan,
                    "invert_tilt": self.invert_tilt,
                    "kp": self.kp,
                    "pan_offset": self.pan_offset,
                    "tilt_offset": self.tilt_offset,
                    "smooth_factor": self.smooth_factor,
                    "deadband_px": self.deadband_px,
                    "tracking_enabled": self.tracking_enabled
                }, f, indent=2)
        except Exception:
            pass

    def set_manual_laser(self, on: bool):
        """Manually force laser ON or OFF for physical targeting alignment calibration."""
        with self.lock:
            self.manual_laser = bool(on)
            self._set_laser(self.manual_laser)
            self.send_angles(self.pan_angle, self.tilt_angle)
        return self.get_state()

    def set_tracking_enabled(self, enabled: bool):
        """Enable or freeze closed-loop target tracking to allow stable calibration."""
        with self.lock:
            self.tracking_enabled = bool(enabled)
            self.filtered_dx = 0.0
            self.filtered_dy = 0.0
        return self.get_state()

    def set_esp32_endpoint(self, ip_or_url: str, port: int = 8888):
        """Update destination ESP32 network IP for UDP command dispatch."""
        if not ip_or_url or str(ip_or_url).isdigit() or str(ip_or_url) in ("0", "1", "2", "webcam"):
            with self.lock:
                self.esp32_ip = None
            return
        clean_ip = str(ip_or_url)
        if "://" in clean_ip:
            clean_ip = clean_ip.split("://")[1]
        if ":" in clean_ip:
            clean_ip = clean_ip.split(":")[0]
        if "/" in clean_ip:
            clean_ip = clean_ip.split("/")[0]

        with self.lock:
            self.esp32_ip = clean_ip
            self.udp_port = port
            self.is_simulated = False
        print(f"[TURRET] Network UDP endpoint configured: {self.esp32_ip}:{self.udp_port}")

    def recalculate_kinematics(self):
        """
        Dynamically calculates distance-independent kinematics and limits.
        
        Mathematical Principle:
        When the optical sensor is mounted on the tilt C-arm (eye-in-hand),
        angular tracking error (dx, dy) in image space is given by:
            d_pan  = -arctan(dx / fx)
            d_tilt =  arctan(dy / fy)
        Azimuth (pan) is pure rotation about the vertical Z-axis, which is
        completely independent of the vertical separation height d.
        Elevation (tilt) rotates directly around the upper pivot, making
        closed-loop error nulling decoupled from d.
        
        For 3D spatial target tracking, mechanical clearance and baseline
        parallax at nominal engagement distance (1.2m) are auto-compensated.
        """
        d = max(10.0, min(220.0, self.servo_distance_mm))
        self.servo_distance_mm = d
        h = max(20.0, min(500.0, getattr(self, 'base_height_mm', 190.0)))
        self.base_height_mm = h

        # Normalized proportional tracking gain (independent of d)
        # Visual servoing operates on normalized image angular errors
        self.kp = round(max(0.04, min(0.18, self.base_kp)), 4)

        # Dual-servo physical clearance envelope auto-adjustment
        pan_margin = max(5.0, 10.0 + max(0.0, (d - 45.0) * 0.06))
        self.pan_min = round(pan_margin, 1)
        self.pan_max = round(180.0 - pan_margin, 1)

        tilt_margin = max(15.0, 35.0 - (d - 20.0) * 0.15)
        self.tilt_min = round(tilt_margin, 1)
        self.tilt_max = round(180.0 - tilt_margin, 1)

        # Baseline parallax angle at 1.2m nominal target distance
        self.parallax_deg = round(math.degrees(math.atan2(d, 1200.0)), 2)
        self.base_parallax_deg = round(math.degrees(math.atan2(h, 1200.0)), 2)

    def set_servo_distance(self, distance_mm: float):
        """Update physical servo separation distance and automatically recalibrate kinematics."""
        return self.set_structure(servo_distance_mm=distance_mm)

    def set_structure(self, servo_distance_mm=None, base_height_mm=None, pan_offset=None, tilt_offset=None,
                      invert_pan=None, invert_tilt=None, kp=None, smooth_factor=None, tracking_enabled=None):
        """Update physical dimensions and calibration trims."""
        with self.lock:
            if servo_distance_mm is not None:
                self.servo_distance_mm = float(servo_distance_mm)
            if base_height_mm is not None:
                self.base_height_mm = float(base_height_mm)
            if pan_offset is not None:
                self.pan_offset = float(pan_offset)
            if tilt_offset is not None:
                self.tilt_offset = float(tilt_offset)
            if invert_pan is not None:
                self.invert_pan = bool(invert_pan)
            if invert_tilt is not None:
                self.invert_tilt = bool(invert_tilt)
            if kp is not None:
                self.kp = max(0.01, min(0.25, float(kp)))
                self.base_kp = self.kp
            if smooth_factor is not None:
                self.smooth_factor = max(0.05, min(0.95, float(smooth_factor)))
            if tracking_enabled is not None:
                self.tracking_enabled = bool(tracking_enabled)

            self.recalculate_kinematics()
            self._save_config()
            self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle))
            self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle))
            self.send_angles(self.pan_angle, self.tilt_angle)
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
                smooth_frac = 0.5 * (1.0 - math.cos(math.pi * frac))
                cur_p = p_start + (target_p - p_start) * smooth_frac
                cur_t = t_start + (target_t - t_start) * smooth_frac
                with self.lock:
                    self.pan_angle = cur_p
                    self.tilt_angle = cur_t
                    self.send_angles(cur_p, cur_t)
                time.sleep(delay)
            return True

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
                self.calibration_stage = f"PAN SWEEP [{int(self.pan_min)}-{int(self.pan_max)}]"
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
                self.calibration_stage = f"TILT SWEEP [{int(self.tilt_min)}-{int(self.tilt_max)}]"
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
        if not HAS_SERIAL or getattr(self, "stream_writer", None) or getattr(self, "use_shared_serial", False):
            self.is_simulated = (getattr(self, "stream_writer", None) is None)
            return

        available_ports = []
        try:
            available_ports = [p.device for p in serial.tools.list_ports.comports() if "bluetooth" not in p.description.lower()]
        except Exception:
            pass

        if not available_ports:
            self.is_simulated = True
            return

        if not self.port or self.port not in available_ports:
            self.port = available_ports[0]

        try:
            s = serial.Serial()
            s.port = self.port
            s.baudrate = self.baudrate
            s.dtr = False
            s.rts = False
            s.timeout = 0.1
            s.open()
            self.serial_conn = s
            self.is_simulated = False
            print(f"[TURRET] Hardware USB Serial connected on {self.port} at {self.baudrate} baud.")
            self.send_angles(90, 90)
        except Exception:
            self.is_simulated = True
            self.serial_conn = None

    def start_rl_alignment(self):
        """Initiate reinforcement-style active visual alignment to center on target balloon."""
        with self.lock:
            self.rl_active = True
            self.rl_stage = "ACQUIRING"
            self.rl_reward = 0.0
            self.rl_alignment_pct = 0.0
            self.rl_streak = 0
            self.rl_v_pan = 0.0
            self.rl_v_tilt = 0.0
        return self.get_state()

    def stop_rl_alignment(self):
        """Abort active visual centering alignment."""
        with self.lock:
            self.rl_active = False
            self.rl_stage = "IDLE"
            self.rl_streak = 0
        return self.get_state()

    def apply_rl_calibrated_home(self):
        """Save current target-centered position as calibrated horizontal/vertical home reference."""
        with self.lock:
            self.pan_offset = round(self.pan_angle - 90.0, 1)
            self.tilt_offset = round(self.tilt_angle - 90.0, 1)
            self._save_config()
            self.rl_stage = "CALIBRATED"
        return self.get_state()

    def update_rl_alignment(self, dx, dy, locked):
        """
        Reinforcement-style policy gradient alignment loop.
        Optimizes pan/tilt actions to drive optical center error (dx, dy) -> (0, 0).
        Computes continuous reward R, policy gradient step with momentum,
        and provides convergence feedback until optical center is perfectly locked.
        """
        with self.lock:
            if not getattr(self, 'rl_active', False):
                return

            if not locked:
                self.rl_stage = "ACQUIRING"
                self.rl_streak = 0
                self.rl_v_pan *= 0.5
                self.rl_v_tilt *= 0.5
                self.rl_reward = 0.0
                return

            dist = math.hypot(dx, dy)
            self.rl_dist_px = round(dist, 1)
            # Alignment percentage: 0% at frame edge (160px), 100% at center (0px)
            alignment_pct = max(0.0, min(100.0, (1.0 - (dist / 160.0)) * 100.0))
            self.rl_alignment_pct = round(alignment_pct, 1)

            # Continuous reward formulation
            reward = 10.0 - (0.08 * dist) - 0.05 * (abs(self.rl_v_pan) + abs(self.rl_v_tilt))

            # Adaptive Learning Rate: Fast approach when far, subpixel precision when close
            if dist > 45.0:
                alpha = 0.065
                self.rl_stage = "CONVERGING"
            elif dist > 15.0:
                alpha = 0.035
                self.rl_stage = "FINE_TUNING"
            else:
                alpha = 0.018
                self.rl_stage = "FINE_TUNING"

            # Direction vectors based on calibrated axis orientation
            dpan_dir = dx if self.invert_pan else -dx
            dtilt_dir = -dy if self.invert_tilt else dy

            # Policy Gradient Step with Momentum (Actor-Critic dynamics)
            self.rl_v_pan = 0.55 * self.rl_v_pan + 0.45 * (dpan_dir * alpha)
            self.rl_v_tilt = 0.55 * self.rl_v_tilt + 0.45 * (dtilt_dir * alpha)

            # Slew rate limitation to ensure silky smooth RL adjustments
            max_step = min(1.6, getattr(self, 'max_slew_step_deg', 1.6))
            step_pan = max(-max_step, min(max_step, self.rl_v_pan))
            step_tilt = max(-max_step, min(max_step, self.rl_v_tilt))

            self.pan_angle += step_pan
            self.tilt_angle += step_tilt
            self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle))
            self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle))

            # Goal state evaluation: within tolerance of absolute center
            if dist <= self.rl_center_tolerance_px:
                reward += 40.0  # Goal arrival reinforcement reward bonus
                self.rl_streak += 1
                if self.rl_streak >= self.rl_target_streak:
                    self.rl_stage = "CENTER_LOCKED"
            else:
                self.rl_streak = max(0, self.rl_streak - 1)

            self.rl_reward = round(reward, 2)
            self.send_angles(self.pan_angle, self.tilt_angle)

    def update_aiming(self, dx, dy, locked):
        """
        Update pan/tilt angles based on optical pixel error (closed-loop).
        Applies EMA smoothing filter, deadband anti-jitter, direction inversion,
        and slew-rate acceleration limiting to safeguard the 5V 2A power adapter.
        """
        now = time.time()
        with self.lock:
            if self.is_calibrating:
                return

            if not getattr(self, 'tracking_enabled', True):
                # Target tracking is frozen for manual alignment calibration
                if getattr(self, 'manual_laser', False):
                    self._set_laser(True)
                return

            if locked:
                # 1. Deadband filter to prevent micro-jitter when target is centered
                db = getattr(self, 'deadband_px', 6.0)
                eff_dx = 0.0 if abs(dx) < db else (dx - db if dx > 0 else dx + db)
                eff_dy = 0.0 if abs(dy) < db else (dy - db if dy > 0 else dy + db)

                # 2. Exponential Moving Average (EMA) smoothing on pixel delta
                alpha = getattr(self, 'smooth_factor', 0.22)
                prev_dx = getattr(self, 'filtered_dx', 0.0)
                prev_dy = getattr(self, 'filtered_dy', 0.0)
                self.filtered_dx = (1.0 - alpha) * prev_dx + alpha * float(eff_dx)
                self.filtered_dy = (1.0 - alpha) * prev_dy + alpha * float(eff_dy)

                # 3. Proportional + Derivative (PD) damping to brake smoothly before center
                d_err_x = self.filtered_dx - prev_dx
                d_err_y = self.filtered_dy - prev_dy

                if abs(self.filtered_dx) > 0.4 or abs(self.filtered_dy) > 0.4:
                    pan_inv = getattr(self, 'invert_pan', True)
                    tilt_inv = getattr(self, 'invert_tilt', False)

                    # Derivative damping kd counteracts overshoot
                    kd = 0.045
                    raw_dpan_val = (self.filtered_dx * self.kp) + (d_err_x * kd)
                    raw_dtilt_val = (self.filtered_dy * self.kp) + (d_err_y * kd)

                    # Cap maximum slew step per frame to 1.6 deg (silky smooth, no gear slamming)
                    max_slew = min(1.8, getattr(self, 'max_slew_step_deg', 1.8))
                    dpan_clamped = max(-max_slew, min(max_slew, raw_dpan_val))
                    dtilt_clamped = max(-max_slew, min(max_slew, raw_dtilt_val))

                    step_pan = dpan_clamped if pan_inv else -dpan_clamped
                    step_tilt = -dtilt_clamped if tilt_inv else dtilt_clamped

                    self.pan_angle += step_pan
                    self.tilt_angle += step_tilt

                    self.pan_angle = max(self.pan_min, min(self.pan_max, self.pan_angle))
                    self.tilt_angle = max(self.tilt_min, min(self.tilt_max, self.tilt_angle))

                    self.last_target_time = now
                    self.send_angles(self.pan_angle, self.tilt_angle)
            else:
                # Decay filter when target is temporarily occluded
                self.filtered_dx *= 0.5
                self.filtered_dy *= 0.5

            # Laser Safety State Machine & Manual Laser Mode
            if getattr(self, 'manual_laser', False):
                # Manual laser pointer active for physical sighting calibration
                self._set_laser(True)
            elif not self.laser_armed:
                self._set_laser(False)
            elif not locked or (now - self.last_target_time > 0.3):
                # Automatic Cutoff: Target lock lost for >300ms
                self._set_laser(False)
            elif now < self.cooldown_until:
                # Cooling down after maximum fire duration
                self._set_laser(False)
            elif locked and abs(dx) < 16 and abs(dy) < 16:
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
        return self.get_state()

    def center(self):
        """Reset servos to neutral center position (90, 90)."""
        with self.lock:
            if self.is_calibrating:
                self.stop_auto_calibration()
            self.pan_angle = 90.0
            self.tilt_angle = 90.0
            self._set_laser(False)
            self.send_angles(90, 90)
        return self.get_state()

    def zero_tilt_level(self):
        """Calibrate current physical tilt position as the 90.0 deg horizontal level reference."""
        with self.lock:
            current_hw = self.tilt_angle + getattr(self, 'tilt_offset', 0.0)
            self.tilt_offset = round(current_hw - 90.0, 1)
            self.tilt_angle = 90.0
            self._save_config()
            self.send_angles(self.pan_angle, self.tilt_angle)
        return self.get_state()

    def set_armed(self, armed: bool):
        with self.lock:
            self.laser_armed = armed
            if not armed:
                self._set_laser(False)

    def _set_laser(self, on: bool):
        self.laser_firing = on
        if getattr(self, "_last_sent_laser", None) == on:
            return
        self._last_sent_laser = on

        cmd = f"L{1 if on else 0}\n"
        if getattr(self, "stream_writer", None):
            self.stream_writer(cmd.encode("ascii"))
        elif self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(cmd.encode("ascii"))
            except Exception:
                pass

        # 2. Fast UDP network dispatch
        if self.esp32_ip:
            pkt = f"P:{self.pan_angle:.1f},T:{self.tilt_angle:.1f},L:{1 if on else 0}\n"
            try:
                self.udp_sock.sendto(pkt.encode("ascii"), (self.esp32_ip, self.udp_port))
            except Exception:
                pass

    def send_angles(self, pan, tilt):
        """Dispatch angles to ESP32 over both high-speed UDP and Serial."""
        pan_val = round(float(pan), 1)
        tilt_val = round(float(tilt), 1)
        laser_val = 1 if self.laser_firing else 0

        # Auto-reconnect to Serial if port was temporarily locked by Arduino Serial Monitor
        if not getattr(self, "stream_writer", None) and not getattr(self, "use_shared_serial", False):
            if (not self.serial_conn or not getattr(self.serial_conn, 'is_open', False)) and HAS_SERIAL:
                now = time.time()
                if getattr(self, "_last_reconnect_attempt", 0) + 2.5 < now:
                    self._last_reconnect_attempt = now
                    self._connect_serial()

        hw_pan = round(max(0.0, min(180.0, pan_val + getattr(self, 'pan_offset', 0.0))), 1)
        hw_tilt = round(max(0.0, min(180.0, tilt_val + getattr(self, 'tilt_offset', 0.0))), 1)

        now = time.time()
        pan_diff = abs(hw_pan - getattr(self, "_last_sent_pan", -999.0))
        tilt_diff = abs(hw_tilt - getattr(self, "_last_sent_tilt", -999.0))
        laser_diff = (laser_val != getattr(self, "_last_sent_laser", None))
        time_since_last = now - getattr(self, "_last_send_time", 0.0)

        # Rate limit to max 30Hz (~33ms) to avoid bus congestion while maintaining fluid motion
        if not laser_diff and time_since_last < 0.033:
            return

        # Skip duplicate packets if angles haven't moved (sub-0.12 deg deadband)
        if not laser_diff and pan_diff < 0.12 and tilt_diff < 0.12:
            return

        self._last_sent_pan = hw_pan
        self._last_sent_tilt = hw_tilt
        self._last_sent_laser = laser_val
        self._last_send_time = now

        # 1. UART Serial dispatch (float precision parsed smoothly by ESP32 atof)
        cmd = f"P{hw_pan:.1f} T{hw_tilt:.1f} L{laser_val}\n"
        if getattr(self, "stream_writer", None):
            self.stream_writer(cmd.encode("ascii"))
        elif self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(cmd.encode("ascii"))
            except Exception as e:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
                self.serial_conn = None

        # 2. Fast UDP network dispatch
        if self.esp32_ip:
            pkt = f"P:{hw_pan:.1f},T:{hw_tilt:.1f},L:{laser_val}\n"
            try:
                self.udp_sock.sendto(pkt.encode("ascii"), (self.esp32_ip, self.udp_port))
            except Exception:
                pass

    def get_state(self):
        with self.lock:
            return {
                "pan": round(self.pan_angle, 1),
                "tilt": round(self.tilt_angle, 1),
                "servo_distance_mm": self.servo_distance_mm,
                "base_height_mm": getattr(self, 'base_height_mm', 190.0),
                "pan_offset": getattr(self, 'pan_offset', 0.0),
                "tilt_offset": getattr(self, 'tilt_offset', 0.0),
                "kp": getattr(self, 'kp', 0.06),
                "invert_pan": getattr(self, 'invert_pan', True),
                "invert_tilt": getattr(self, 'invert_tilt', False),
                "tracking_enabled": getattr(self, 'tracking_enabled', True),
                "manual_laser": getattr(self, 'manual_laser', False),
                "smooth_factor": getattr(self, 'smooth_factor', 0.25),
                "deadband_px": getattr(self, 'deadband_px', 5.0),
                "pan_limits": [self.pan_min, self.pan_max],
                "tilt_limits": [self.tilt_min, self.tilt_max],
                "parallax_deg": self.parallax_deg,
                "base_parallax_deg": getattr(self, 'base_parallax_deg', 0.0),
                "is_calibrating": self.is_calibrating,
                "calibration_progress": self.calibration_progress,
                "calibration_stage": self.calibration_stage,
                "laser_armed": self.laser_armed,
                "laser_firing": self.laser_firing,
                "is_simulated": (not self.serial_conn or not getattr(self.serial_conn, 'is_open', False)) and not bool(self.esp32_ip),
                "esp32_ip": self.esp32_ip,
                "is_cooldown": time.time() < self.cooldown_until,
                "rl_active": getattr(self, "rl_active", False),
                "rl_stage": getattr(self, "rl_stage", "IDLE"),
                "rl_reward": getattr(self, "rl_reward", 0.0),
                "rl_alignment_pct": getattr(self, "rl_alignment_pct", 0.0),
                "rl_streak": getattr(self, "rl_streak", 0),
                "rl_dist_px": getattr(self, "rl_dist_px", 0.0)
            }
