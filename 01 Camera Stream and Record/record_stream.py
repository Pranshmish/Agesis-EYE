"""
ESP32-CAM MJPEG Stream Recorder — Optimized for sustained recording.
Uses requests + iter_content for robust chunked HTTP handling.
Auto-reconnects on any disconnect. Dedicated writer thread.
"""
import cv2
import time
import os
import argparse
import sys
import json
import threading
import queue
import numpy as np

try:
    import requests
except ImportError:
    print("[!] Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests


class StreamReader:
    """Background MJPEG reader with auto-reconnect."""

    def __init__(self, url):
        self.url = url
        self.latest_frame = None
        self.frame_queue = queue.Queue(maxsize=500)
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.total_frames = 0
        self.fps = 0.0
        self.reconnects = 0
        self.last_error = ""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running:
            try:
                self._stream_loop()
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
            # Wait before reconnecting
            if self.running:
                self.reconnects += 1
                print(f"[Stream] Reconnecting (#{self.reconnects})...")
                for _ in range(6):  # 3 second wait, interruptible
                    if not self.running:
                        return
                    time.sleep(0.5)

    def _stream_loop(self):
        sess = requests.Session()
        resp = sess.get(self.url, stream=True, timeout=(5, 10))
        resp.raise_for_status()
        self.connected = True
        print(f"[Stream] Connected to {self.url}")

        buf = b''
        fc = 0
        t0 = time.time()

        try:
            for chunk in resp.iter_content(chunk_size=4096):
                if not self.running:
                    break
                buf += chunk

                # Extract all complete JPEG frames from buffer
                while True:
                    a = buf.find(b'\xff\xd8')
                    if a == -1:
                        buf = buf[-2:] if len(buf) > 2 else buf  # keep tail for split marker
                        break
                    b = buf.find(b'\xff\xd9', a + 2)
                    if b == -1:
                        buf = buf[a:]  # keep from SOI onward
                        break

                    jpg = buf[a:b + 2]
                    buf = buf[b + 2:]

                    frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    self.total_frames += 1
                    fc += 1
                    elapsed = time.time() - t0
                    if elapsed >= 1.0:
                        self.fps = fc / elapsed
                        fc = 0
                        t0 = time.time()

                    with self.lock:
                        self.latest_frame = frame

                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                        self.frame_queue.put_nowait(frame)
        finally:
            self.connected = False
            try:
                resp.close()
            except Exception:
                pass
            try:
                sess.close()
            except Exception:
                pass

    def get_latest(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def read(self):
        f = self.get_latest()
        return (f is not None, f)

    def isOpened(self):
        deadline = time.time() + 15.0
        while time.time() < deadline:
            if self.get_latest() is not None:
                return True
            time.sleep(0.2)
        return False

    def release(self):
        self.running = False


class VideoWriterThread:
    """Writes frames from a queue to an AVI file in a background thread."""

    def __init__(self, path, fourcc, fps, size):
        self.writer = cv2.VideoWriter(path, fourcc, fps, size)
        self.q = queue.Queue(maxsize=500)
        self.count = 0
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running or not self.q.empty():
            try:
                frame = self.q.get(timeout=0.1)
                self.writer.write(frame)
                self.count += 1
            except queue.Empty:
                continue

    def write(self, frame):
        try:
            self.q.put_nowait(frame)
        except queue.Full:
            pass  # Drop frame rather than block

    def release(self):
        self.running = False
        self._thread.join(timeout=3)
        self.writer.release()


def parse_args():
    p = argparse.ArgumentParser(description="ESP32-CAM Stream Recorder")
    p.add_argument("--ip", default="")
    p.add_argument("--port", default="81")
    p.add_argument("--path", default="stream")
    p.add_argument("--tag", default="session")
    p.add_argument("--fps", type=int, default=15)
    p.add_argument("--duration", type=float, default=0)
    p.add_argument("--outdir", default="raw_video")
    return p.parse_args()


def get_stream_url(ip, port, path):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_config.json")
    if not ip and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                ip = json.load(f).get("ip", "")
                if ip:
                    print(f"[+] Loaded IP from camera_config.json: {ip}")
        except Exception:
            pass
    if not ip:
        ip = input("Enter ESP32-CAM IP: ").strip()
    if port and port not in ("80", ""):
        return f"http://{ip}:{port}/{path.lstrip('/')}", ip
    return f"http://{ip}/{path.lstrip('/')}", ip


def main():
    args = parse_args()
    url, ip = get_stream_url(args.ip, args.port, args.path)
    os.makedirs(args.outdir, exist_ok=True)

    print(f"\n[+] Connecting to: {url}")
    print("[!] Press 'q' or ESC to stop.\n")

    reader = StreamReader(url)

    if not reader.isOpened():
        print(f"\n[ERROR] Cannot connect to {url}")
        if reader.last_error:
            print(f"  Reason: {reader.last_error}")
        print("  - Is the ESP32-CAM powered on?")
        print("  - Are laptop and ESP32 on the same WiFi?")
        print("  - Close all other browser tabs accessing the camera")
        reader.release()
        sys.exit(1)

    frame = reader.get_latest()
    h, w = frame.shape[:2]
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(args.outdir, f"{ts}_{args.tag}_{w}x{h}.avi")

    writer = VideoWriterThread(out_file, cv2.VideoWriter_fourcc(*"MJPG"), args.fps, (w, h))

    print(f"[+] Resolution: {w}x{h}")
    print(f"[+] Recording to: {out_file}")

    start = time.time()
    last_hud = time.time()
    hud_fps = 0.0

    try:
        while True:
            # Drain all queued frames to writer
            while not reader.frame_queue.empty():
                try:
                    writer.write(reader.frame_queue.get_nowait())
                except queue.Empty:
                    break

            # Display latest frame
            frame = reader.get_latest()
            if frame is None:
                time.sleep(0.01)
                continue

            now = time.time()
            elapsed = now - start

            if now - last_hud >= 0.5:
                hud_fps = writer.count / max(0.001, elapsed)
                last_hud = now

            # HUD overlay
            tag = f"REC [{args.tag}] {elapsed:.0f}s | {writer.count} frames | {hud_fps:.1f} FPS"
            cv2.circle(frame, (18, 22), 7, (0, 0, 255), -1)
            cv2.putText(frame, tag, (34, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            status = f"Cam: {reader.fps:.0f} FPS" + ("  [RECONNECTING]" if not reader.connected else "")
            cv2.putText(frame, status, (18, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            cv2.imshow("ESP32-CAM Recorder", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            if args.duration > 0 and elapsed >= args.duration:
                break

    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
    finally:
        # Drain remaining
        while not reader.frame_queue.empty():
            try:
                writer.write(reader.frame_queue.get_nowait())
            except queue.Empty:
                break

        reader.release()
        writer.release()
        cv2.destroyAllWindows()

        dt = time.time() - start
        print(f"\n[+] Done! Saved: {out_file}")
        print(f"    Frames: {writer.count} | Duration: {dt:.1f}s | Avg FPS: {writer.count / max(0.001, dt):.1f}")
        if reader.reconnects > 0:
            print(f"    Stream reconnects: {reader.reconnects}")


if __name__ == "__main__":
    main()
