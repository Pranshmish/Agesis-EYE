"""
Agesis EYE - Web Application Server
FastAPI asynchronous backend serving live MJPEG stream, WebSocket telemetry, and control APIs.
"""

import os
import sys
import json
import time
import threading
import asyncio
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Resolve paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from tracker import ZeroLagStreamReader, BalloonTracker, auto_discover_esp32_ip
from turret import TurretController

PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
CONFIG_PATH = os.path.join(BACKEND_DIR, "camera_config.json")
SNAPSHOT_DIR = os.path.join(BACKEND_DIR, "snapshots")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Select best model: prioritize ONNX, fallback to PyTorch
model_candidates = [
    os.path.join(BACKEND_DIR, "models", "agesis06.onnx"),
    os.path.join(BACKEND_DIR, "models", "agesis06.pt"),
]
MODEL_PATH = next((p for p in model_candidates if os.path.exists(p)), model_candidates[0])

# Load camera config
default_stream_url = "COM15"
flip_v = True
flip_h = False
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
            default_stream_url = cfg.get("stream_url", default_stream_url)
            flip_v = cfg.get("flip_v", True)
            flip_h = cfg.get("flip_h", False)
    except Exception:
        pass

# Initialize Components
stream_reader = ZeroLagStreamReader(default_stream_url)
tracker = BalloonTracker(MODEL_PATH, imgsz=384, conf=0.22, enhance=True)
is_serial_stream = stream_reader.is_serial
turret = TurretController(esp32_ip=None, use_shared_serial=is_serial_stream)
if str(default_stream_url).startswith("http"):
    turret.set_esp32_endpoint(default_stream_url)
elif stream_reader.is_serial:
    turret.use_shared_serial = True
    turret.stream_writer = stream_reader.write_serial
    turret.is_simulated = False

app = FastAPI(title="Agesis EYE Autonomous Turret")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Telemetry Cache
latest_telemetry = {
    "locked": False,
    "streak": 0,
    "dx": 0,
    "dy": 0,
    "conf": 0.0,
    "target_pos": "NONE",
    "latency_ms": 0.0,
    "enhance": False,
    "conf_threshold": 0.22,
    "cam_fps": 0.0,
    "connected": False,
    "flip_v": flip_v,
    "flip_h": flip_h,
    **turret.get_state()
}


# Shared state for decoupled ultra-low latency tracking & streaming
latest_jpeg_bytes = None
latest_frame_id = 0
frame_lock = threading.Lock()
new_frame_event = threading.Event()


def tracking_pipeline_worker():
    """Continuous high-frequency tracking pipeline running independently of client connections."""
    global latest_telemetry, latest_jpeg_bytes, latest_frame_id
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
    last_processed_fid = -1

    standby = cv2.imread(os.path.join(BACKEND_DIR, "standby.jpg"))
    if standby is None:
        standby = 20 * np.ones((240, 320, 3), dtype=np.uint8)
        cv2.putText(standby, "ACQUIRING STREAM...", (35, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (35, 25, 255), 1)
    _, standby_jpeg = cv2.imencode(".jpg", standby, encode_param)
    standby_bytes = standby_jpeg.tobytes()

    while True:
        frame, fid = stream_reader.get_latest()
        if frame is None:
            latest_telemetry.update({
                **turret.get_state(),
                "connected": stream_reader.connected,
                "cam_fps": round(stream_reader.fps, 1),
            })
            with frame_lock:
                latest_jpeg_bytes = standby_bytes
                latest_frame_id += 1
            time.sleep(0.04)
            continue

        if fid == last_processed_fid:
            # Yield CPU to allow video capture thread and serial I/O to run smoothly
            time.sleep(0.003)
            continue

        last_processed_fid = fid

        # Apply camera feed flip (V-Flip upside down for inverted ESP32-CAM lens mounting)
        if flip_v and flip_h:
            frame = cv2.flip(frame, -1)
        elif flip_v:
            frame = cv2.flip(frame, 0)
        elif flip_h:
            frame = cv2.flip(frame, 1)

        annotated, tele = tracker.process_frame(frame)

        if getattr(turret, 'rl_active', False):
            turret.update_rl_alignment(tele["dx"], tele["dy"], tele["locked"])
            # Draw Reinforcement Alignment Overlay on annotated video
            h_f, w_f = annotated.shape[:2]
            cx, cy = w_f // 2, h_f // 2
            rl_st = turret.get_state()
            if tele["locked"]:
                tx = int(cx + tele["dx"])
                ty = int(cy + tele["dy"])
                cv2.line(annotated, (cx, cy), (tx, ty), (0, 255, 255), 2)
                cv2.circle(annotated, (tx, ty), 6, (0, 255, 255), -1)
            badge_text = f"RL ALIGN: {rl_st['rl_alignment_pct']}% | R: {rl_st['rl_reward']} | {rl_st['rl_stage']}"
            cv2.putText(annotated, badge_text, (15, h_f - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
        else:
            turret.update_aiming(tele["dx"], tele["dy"], tele["locked"])

        turret_state = turret.get_state()
        latest_telemetry = {
            **tele,
            **turret_state,
            "cam_fps": round(stream_reader.fps, 1),
            "connected": stream_reader.connected,
            "flip_v": flip_v,
            "flip_h": flip_h
        }

        ret, jpeg = cv2.imencode(".jpg", annotated, encode_param)
        if ret:
            with frame_lock:
                latest_jpeg_bytes = jpeg.tobytes()
                latest_frame_id += 1


# Start tracking pipeline thread immediately
_tracking_thread = threading.Thread(target=tracking_pipeline_worker, daemon=True)
_tracking_thread.start()


async def mjpeg_generator():
    """Zero-lag asynchronous MJPEG stream generator for HTML <img>."""
    global latest_jpeg_bytes, latest_frame_id
    last_sent_id = -1

    while True:
        with frame_lock:
            curr_id = latest_frame_id
            curr_bytes = latest_jpeg_bytes

        if curr_bytes is not None and curr_id != last_sent_id:
            last_sent_id = curr_id
            frame_len = len(curr_bytes)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(frame_len).encode("ascii") + b"\r\n\r\n"
                + curr_bytes + b"\r\n"
            )
            await asyncio.sleep(0.015)
        else:
            await asyncio.sleep(0.02)


@app.get("/api/stream")
async def video_stream():
    """MJPEG stream endpoint for live video playback in HTML <img>."""
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, pre-check=0, post-check=0, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Access-Control-Allow-Origin": "*",
    }
    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers=headers
    )


@app.get("/api/frame/latest")
def get_latest_frame():
    """Ultra-low latency single-frame snapshot endpoint for canvas/image fallback."""
    with frame_lock:
        curr_bytes = latest_jpeg_bytes
    if curr_bytes is None:
        return Response(status_code=503, content="No frame ready")
    return Response(
        content=curr_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/api/telemetry")
def get_telemetry():
    """REST API endpoint for real-time tracking metrics."""
    return latest_telemetry


class ConfigModel(BaseModel):
    conf: float = None
    enhance: bool = None
    source: str = None
    laser_armed: bool = None
    flip_v: bool = None
    flip_h: bool = None


@app.post("/api/config")
def update_config(cfg: ConfigModel):
    """Update runtime tracking parameters."""
    global stream_reader, flip_v, flip_h
    if cfg.conf is not None:
        tracker.conf = max(0.10, min(0.95, float(cfg.conf)))
    if cfg.enhance is not None:
        tracker.enhance = bool(cfg.enhance)
    if cfg.laser_armed is not None:
        turret.set_armed(bool(cfg.laser_armed))
    if cfg.flip_v is not None:
        flip_v = bool(cfg.flip_v)
    if cfg.flip_h is not None:
        flip_h = bool(cfg.flip_h)
    if cfg.source is not None and cfg.source != stream_reader.source:
        stream_reader.release()
        stream_reader = ZeroLagStreamReader(cfg.source)
        if str(cfg.source).startswith("http"):
            turret.set_esp32_endpoint(cfg.source)
            turret.use_shared_serial = False
            turret.stream_writer = None
        elif stream_reader.is_serial:
            turret.set_esp32_endpoint(None)
            turret.use_shared_serial = True
            turret.stream_writer = stream_reader.write_serial
            turret.is_simulated = False
        else:
            turret.set_esp32_endpoint(None)
            turret.use_shared_serial = False
            turret.stream_writer = None
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({
                "stream_url": stream_reader.source,
                "flip_v": flip_v,
                "flip_h": flip_h
            }, f, indent=2)
    except Exception:
        pass
    return {"status": "ok", "telemetry": latest_telemetry}


class DistanceModel(BaseModel):
    distance_mm: float


class StructureModel(BaseModel):
    servo_distance_mm: float = None
    base_height_mm: float = None
    pan_offset: float = None
    tilt_offset: float = None
    invert_pan: bool = None
    invert_tilt: bool = None
    kp: float = None
    smooth_factor: float = None
    tracking_enabled: bool = None


@app.post("/api/turret/distance")
def set_servo_distance(d: DistanceModel):
    """Adjust physical distance between the 2 servos and auto-recalibrate kinematics."""
    state = turret.set_servo_distance(d.distance_mm)
    return state


@app.post("/api/turret/structure")
def set_turret_structure(s: StructureModel):
    """Calibrate physical structure dimensions, direction inversions, and servo home trims."""
    state = turret.set_structure(
        servo_distance_mm=s.servo_distance_mm,
        base_height_mm=s.base_height_mm,
        pan_offset=s.pan_offset,
        tilt_offset=s.tilt_offset,
        invert_pan=s.invert_pan,
        invert_tilt=s.invert_tilt,
        kp=s.kp,
        smooth_factor=s.smooth_factor,
        tracking_enabled=s.tracking_enabled
    )
    return state


class ManualLaserModel(BaseModel):
    manual_laser: bool


@app.post("/api/turret/laser/manual")
def set_manual_laser(m: ManualLaserModel):
    """Force manual sighting laser ON or OFF for physical sighting alignment calibration."""
    return turret.set_manual_laser(m.manual_laser)


class TrackingToggleModel(BaseModel):
    tracking_enabled: bool


@app.post("/api/turret/tracking/toggle")
def toggle_turret_tracking(t: TrackingToggleModel):
    """Lock/freeze target tracking to hold turret still during calibration."""
    return turret.set_tracking_enabled(t.tracking_enabled)


@app.post("/api/turret/home")
def home_turret():
    """Calibrate servos directly to physical home/neutral center position (90, 90)."""
    return turret.center()


@app.post("/api/turret/calibrate/zero_tilt")
def zero_tilt_level():
    """Calibrate current physical tilt position as the 90.0 deg horizontal level reference."""
    return turret.zero_tilt_level()


@app.post("/api/turret/calibrate/start")
def start_turret_calibration():
    """Start autonomous 2-servo calibration movement."""
    started = turret.start_auto_calibration()
    return {"status": "started" if started else "already_running", "turret": turret.get_state()}


@app.post("/api/turret/calibrate/stop")
def stop_turret_calibration():
    """Halt active calibration sequence and center servos."""
    state = turret.stop_auto_calibration()
    return {"status": "stopped", "turret": state}


@app.post("/api/turret/alignment/start")
def start_rl_alignment():
    """Initiate active visual reinforcement alignment until target balloon is centered."""
    state = turret.start_rl_alignment()
    return {"status": "started", "turret": state}


@app.post("/api/turret/alignment/stop")
def stop_rl_alignment():
    """Stop active visual reinforcement alignment."""
    state = turret.stop_rl_alignment()
    return {"status": "stopped", "turret": state}


@app.post("/api/turret/alignment/calibrate")
def apply_rl_calibrated_home():
    """Save current target-centered position as calibrated reference home."""
    state = turret.apply_rl_calibrated_home()
    return {"status": "calibrated", "turret": state}


class NudgeModel(BaseModel):
    pan: float = 0.0
    tilt: float = 0.0


@app.post("/api/turret/nudge")
def nudge_turret(n: NudgeModel):
    turret.nudge(n.pan, n.tilt)
    return turret.get_state()


@app.post("/api/turret/center")
def center_turret():
    turret.center()
    return turret.get_state()


@app.post("/api/snapshot")
def take_snapshot():
    res = stream_reader.get_latest()
    if res is None or res[0] is None:
        return JSONResponse({"status": "error", "message": "No active video frame"}, status_code=400)
    frame, _ = res
    annotated, _ = tracker.process_frame(frame)
    fname = f"snap_{int(time.time()*1000)}.jpg"
    fpath = os.path.join(SNAPSHOT_DIR, fname)
    cv2.imwrite(fpath, annotated)
    return {"status": "ok", "filename": fname, "url": f"/snapshots/{fname}"}


@app.get("/api/discover")
def discover_camera():
    discovered = auto_discover_esp32_ip()
    if discovered:
        turret.set_esp32_endpoint(discovered)
        return {"status": "found", "url": discovered, "mode": "network"}
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            desc = p.description.lower()
            if any(k in desc for k in ["cp210", "ch340", "ftdi", "uart", "usb-serial", "serial", "esp"]):
                return {"status": "found", "url": p.device, "mode": "usb"}
    except Exception:
        pass
    return {"status": "not_found", "message": "Could not locate ESP32 on local network or USB"}


@app.websocket("/ws/telemetry")
async def websocket_telemetry(ws: WebSocket):
    """Ultra-low latency WebSocket pipe for 30 FPS HUD telemetry updates."""
    await ws.accept()
    try:
        while True:
            data = json.dumps(
                latest_telemetry,
                default=lambda o: int(o) if isinstance(o, (np.integer, np.int64, np.int32)) else (
                    float(o) if isinstance(o, (np.floating, np.float32, np.float64)) else str(o)
                )
            )
            await ws.send_text(data)
            await asyncio.sleep(0.04)  # 25 Hz updates
    except WebSocketDisconnect:
        pass


# Serve snapshots directory
app.mount("/snapshots", StaticFiles(directory=SNAPSHOT_DIR), name="snapshots")

# Serve complete documentation and PDF manual
DOCS_PATH = os.path.join(PROJECT_ROOT, "docs")
if os.path.exists(DOCS_PATH):
    app.mount("/docs", StaticFiles(directory=DOCS_PATH, html=True), name="docs")

# Serve frontend directory (prioritize compiled React production build in dist/)
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")
static_dir = FRONTEND_DIST if os.path.exists(FRONTEND_DIST) else FRONTEND_DIR
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*58)
    print("  🚀 AGESIS EYE - TACTICAL WEB GROUND STATION")
    print("  Web Interface : http://127.0.0.1:8000")
    print(f"  Model Loaded  : {os.path.basename(MODEL_PATH)}")
    print(f"  Stream Source : {default_stream_url}")
    print("="*58 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
