"""
Live Dataset Collector — Capture frames directly from ESP32-CAM stream.

Usage:
    python collect_live.py                           # Default session
    python collect_live.py --session daylight_near    # Named session
    python collect_live.py --session negative --negative  # Negative frames (no balloon)
    python collect_live.py --auto 0.7                # Auto-capture every 0.7s

Controls:
    SPACE  = Capture frame
    N      = Toggle negative mode (no balloon → empty label)
    A      = Toggle auto-capture mode
    +/-    = Adjust auto-capture interval
    Q/ESC  = Quit and show summary
"""
import cv2
import time
import os
import sys
import json
import argparse
import threading
import queue
import numpy as np

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests


class StreamReader:
    """Same proven reader from Stage 01."""

    def __init__(self, url):
        self.url = url
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.fps = 0.0
        self.last_error = ""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running:
            try:
                sess = requests.Session()
                resp = sess.get(self.url, stream=True, timeout=(5, 10))
                resp.raise_for_status()
                self.connected = True

                buf = b''
                fc = 0
                t0 = time.time()

                for chunk in resp.iter_content(chunk_size=4096):
                    if not self.running:
                        break
                    buf += chunk
                    while True:
                        a = buf.find(b'\xff\xd8')
                        if a == -1:
                            buf = buf[-2:] if len(buf) > 2 else buf
                            break
                        b = buf.find(b'\xff\xd9', a + 2)
                        if b == -1:
                            buf = buf[a:]
                            break
                        jpg = buf[a:b + 2]
                        buf = buf[b + 2:]
                        frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            fc += 1
                            elapsed = time.time() - t0
                            if elapsed >= 1.0:
                                self.fps = fc / elapsed
                                fc = 0
                                t0 = time.time()
                            with self.lock:
                                self.latest_frame = frame

                self.connected = False
                resp.close()
                sess.close()
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
            if self.running:
                for _ in range(6):
                    if not self.running:
                        return
                    time.sleep(0.5)

    def get_latest(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def release(self):
        self.running = False


def get_stream_url():
    """Find camera config from Stage 01."""
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01 Camera Stream and Record", "camera_config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_config.json"),
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    cfg = json.load(f)
                    url = cfg.get("stream_url", "")
                    if url:
                        print(f"[+] Using stream: {url}")
                        return url
            except Exception:
                pass
    ip = input("Enter ESP32-CAM IP: ").strip()
    return f"http://{ip}:81/stream"


def parse_args():
    p = argparse.ArgumentParser(description="Live Dataset Collector from ESP32-CAM")
    p.add_argument("--session", default="session_01", help="Session name (e.g. daylight_near, negative_room)")
    p.add_argument("--negative", action="store_true", help="Mark all captures as negative (no balloon)")
    p.add_argument("--auto", type=float, default=0, help="Auto-capture interval in seconds (0=manual)")
    p.add_argument("--outdir", default="raw_frames", help="Output directory for frames")
    p.add_argument("--videodir", default="raw_video", help="Output directory for full video (default: raw_video)")
    p.add_argument("--no-video", action="store_true", help="Disable simultaneous continuous video recording")
    return p.parse_args()


def main():
    args = parse_args()
    url = get_stream_url()

    session_dir = os.path.join(args.outdir, args.session)
    os.makedirs(session_dir, exist_ok=True)

    print(f"\n[+] Session: {args.session}")
    print(f"[+] Output:  {session_dir}")
    print(f"[+] Connecting to stream...")
    print(f"\n    SPACE = Capture | N = Toggle negative | A = Toggle auto | Q = Quit\n")

    reader = StreamReader(url)

    # Wait for connection
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if reader.get_latest() is not None:
            break
        time.sleep(0.2)

    if reader.get_latest() is None:
        print(f"[ERROR] Cannot connect to {url}")
        reader.release()
        sys.exit(1)

    print("[+] Stream connected!")

    is_negative = args.negative
    auto_capture = args.auto > 0
    auto_interval = args.auto if args.auto > 0 else 0.7
    last_auto_capture = 0
    captured = 0
    existing = len([f for f in os.listdir(session_dir) if f.endswith('.jpg')])

    record_video = not args.no_video
    video_writer = None
    video_path = None
    video_frames_count = 0

    first_frame = reader.get_latest()
    if first_frame is not None and record_video:
        fh, fw = first_frame.shape[:2]
        os.makedirs(args.videodir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(args.videodir, f"{ts}_{args.session}_{fw}x{fh}.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (fw, fh))
        print(f"[+] Recording video to: {video_path}")

    try:
        while True:
            frame = reader.get_latest()
            if frame is None:
                time.sleep(0.01)
                continue

            # Record frame to continuous video
            if video_writer is not None and record_video:
                video_writer.write(frame)
                video_frames_count += 1

            display = frame.copy()
            h, w = display.shape[:2]
            now = time.time()

            # Auto-capture logic
            should_capture = False
            if auto_capture and (now - last_auto_capture) >= auto_interval:
                should_capture = True

            # HUD
            mode_text = "NEGATIVE" if is_negative else "POSITIVE"
            mode_color = (0, 0, 255) if is_negative else (0, 255, 0)
            cv2.putText(display, f"[{mode_text}]", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

            cap_mode = f"AUTO {auto_interval:.1f}s" if auto_capture else "MANUAL (SPACE)"
            cv2.putText(display, cap_mode, (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            if record_video:
                cv2.circle(display, (w - 75, 20), 6, (0, 0, 255), -1)
                cv2.putText(display, "REC", (w - 62, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            info = f"Session: {args.session} | Captured: {existing + captured} | Stream: {reader.fps:.0f} FPS"
            cv2.putText(display, info, (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)

            if not reader.connected:
                cv2.putText(display, "[RECONNECTING...]", (w // 2 - 80, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.imshow("Live Dataset Collector", display)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord('q'), 27):
                break
            elif key == ord(' '):
                should_capture = True
            elif key == ord('n'):
                is_negative = not is_negative
                print(f"  Mode: {'NEGATIVE' if is_negative else 'POSITIVE'}")
            elif key == ord('a'):
                auto_capture = not auto_capture
                print(f"  Auto-capture: {'ON' if auto_capture else 'OFF'} ({auto_interval:.1f}s)")
            elif key == ord('r'):
                record_video = not record_video
                print(f"  Video recording: {'ON' if record_video else 'OFF'}")
            elif key == ord('+') or key == ord('='):
                auto_interval = min(5.0, auto_interval + 0.1)
                print(f"  Auto interval: {auto_interval:.1f}s")
            elif key == ord('-'):
                auto_interval = max(0.2, auto_interval - 0.1)
                print(f"  Auto interval: {auto_interval:.1f}s")

            if should_capture:
                idx = existing + captured
                img_name = f"{args.session}_{idx:05d}.jpg"
                img_path = os.path.join(session_dir, img_name)
                cv2.imwrite(img_path, frame)

                # Create metadata file
                meta = {
                    "session": args.session,
                    "negative": is_negative,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "index": idx
                }
                meta_path = img_path.replace('.jpg', '.json')
                with open(meta_path, 'w') as f:
                    json.dump(meta, f)

                captured += 1
                last_auto_capture = now

                # Flash green border on capture
                cv2.rectangle(display, (0, 0), (w - 1, h - 1), (0, 255, 0), 4)
                cv2.imshow("Live Dataset Collector", display)
                cv2.waitKey(50)

    except KeyboardInterrupt:
        pass
    finally:
        reader.release()
        if video_writer is not None:
            video_writer.release()
        cv2.destroyAllWindows()

        print(f"\n{'=' * 40}")
        print(f"  Session: {args.session}")
        print(f"  Frames captured: {captured}")
        print(f"  Total in session: {existing + captured}")
        print(f"  Saved to: {session_dir}")
        if video_path and video_frames_count > 0:
            print(f"  Video saved: {video_path} ({video_frames_count} frames)")
        print(f"{'=' * 40}")


if __name__ == "__main__":
    main()
