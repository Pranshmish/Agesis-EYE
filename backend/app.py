"""
Agesis EYE - Web Application Server
FastAPI asynchronous backend serving live MJPEG stream, WebSocket telemetry, and control APIs.
"""

import os
import sys
import json
import time
import asyncio
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
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
default_stream_url = "http://10.96.117.1:81/stream"
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
            default_stream_url = cfg.get("stream_url", default_stream_url)
    except Exception:
        pass

# Initialize Components
stream_reader = ZeroLagStreamReader(default_stream_url)
tracker = BalloonTracker(MODEL_PATH, imgsz=384, conf=0.35, enhance=False)
turret = TurretController()
turret.set_esp32_endpoint(default_stream_url)

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
    "conf_threshold": 0.35,
    "cam_fps": 0.0,
    "connected": False,
    **turret.get_state()
}


def mjpeg_generator():
    """Continuously processes freshest frame, runs YOLO, updates turret, and yields MJPEG."""
    global latest_telemetry
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]

    while True:
        frame = stream_reader.get_latest()
        if frame is None:
            # Standby blank frame with connecting status
            latest_telemetry.update({
                **turret.get_state(),
                "connected": stream_reader.connected,
                "cam_fps": round(stream_reader.fps, 1),
            })
            standby = cv2.imread(os.path.join(BACKEND_DIR, "standby.jpg"))
            if standby is None:
                standby = 20 * np.ones((240, 320, 3), dtype=np.uint8)
                cv2.putText(standby, "ACQUIRING STREAM...", (35, 125),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (35, 25, 255), 1)
            _, jpeg = cv2.imencode(".jpg", standby, encode_param)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
            time.sleep(0.04)
            continue

        annotated, tele = tracker.process_frame(frame)
        turret.update_aiming(tele["dx"], tele["dy"], tele["locked"])

        # Update cached state
        turret_state = turret.get_state()
        latest_telemetry = {
            **tele,
            **turret_state,
            "cam_fps": round(stream_reader.fps, 1),
            "connected": stream_reader.connected
        }

        ret, jpeg = cv2.imencode(".jpg", annotated, encode_param)
        if ret:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
        time.sleep(0.005)


import numpy as np


@app.get("/api/stream")
def video_stream():
    """MJPEG stream endpoint for live video playback in HTML <img>."""
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/telemetry")
def get_telemetry():
    """REST API endpoint for real-time tracking metrics."""
    return latest_telemetry


class ConfigModel(BaseModel):
    conf: float = None
    enhance: bool = None
    source: str = None
    laser_armed: bool = None


@app.post("/api/config")
def update_config(cfg: ConfigModel):
    """Update runtime tracking parameters."""
    global stream_reader
    if cfg.conf is not None:
        tracker.conf = max(0.10, min(0.95, float(cfg.conf)))
    if cfg.enhance is not None:
        tracker.enhance = bool(cfg.enhance)
    if cfg.laser_armed is not None:
        turret.set_armed(bool(cfg.laser_armed))
    if cfg.source is not None and cfg.source != stream_reader.source:
        stream_reader.release()
        stream_reader = ZeroLagStreamReader(cfg.source)
        turret.set_esp32_endpoint(cfg.source)
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump({"stream_url": cfg.source}, f, indent=2)
        except Exception:
            pass
    return {"status": "ok", "telemetry": latest_telemetry}


class DistanceModel(BaseModel):
    distance_mm: float


@app.post("/api/turret/distance")
def set_servo_distance(d: DistanceModel):
    """Adjust physical distance between the 2 servos and auto-recalibrate kinematics."""
    state = turret.set_servo_distance(d.distance_mm)
    return state


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
    frame = stream_reader.get_latest()
    if frame is None:
        return JSONResponse({"status": "error", "message": "No active video frame"}, status_code=400)
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
        return {"status": "found", "url": discovered}
    return {"status": "not_found", "message": "Could not locate ESP32 on local subnet"}


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
