"""
Extract Frames from Recorded Videos — For dataset building from Stage 01 recordings.

Usage:
    python extract_frames.py                              # All videos in raw_video/
    python extract_frames.py --video ../01*/raw_video/daylight.avi
    python extract_frames.py --interval 1.0               # 1 frame per second
    python extract_frames.py --session daylight_near       # Custom session name

Extracts frames at configurable intervals, skipping near-duplicate consecutive frames.
"""
import cv2
import os
import sys
import argparse
import glob


def parse_args():
    p = argparse.ArgumentParser(description="Extract frames from recorded videos")
    p.add_argument("--video", type=str, default="", help="Path to a specific video file")
    p.add_argument("--videodir", type=str, default="",
                   help="Directory of videos to process (default: ../01 Camera Stream and Record/raw_video/)")
    p.add_argument("--interval", type=float, default=0.7,
                   help="Seconds between extracted frames (default: 0.7)")
    p.add_argument("--session", type=str, default="",
                   help="Override session name (default: derived from video filename)")
    p.add_argument("--outdir", type=str, default="raw_frames",
                   help="Output directory (default: raw_frames)")
    return p.parse_args()


def extract_from_video(video_path, outdir, interval, session_name=""):
    """Extract frames from a single video file."""
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        return 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open: {video_path}")
        return 0

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 15  # Fallback for MJPEG streams that don't report FPS
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Session name from filename if not provided
    if not session_name:
        basename = os.path.splitext(os.path.basename(video_path))[0]
        # Remove timestamp prefix like "20261002_001408_"
        parts = basename.split('_')
        if len(parts) >= 3 and parts[0].isdigit():
            session_name = '_'.join(parts[2:])
        else:
            session_name = basename

    session_dir = os.path.join(outdir, session_name)
    os.makedirs(session_dir, exist_ok=True)

    step = max(1, int(fps * interval))
    frame_idx = 0
    saved = 0
    existing = len([f for f in os.listdir(session_dir) if f.endswith('.jpg')])

    print(f"\n[+] Processing: {os.path.basename(video_path)}")
    print(f"    FPS: {fps:.1f} | Total frames: {total_frames} | Step: every {step} frames ({interval}s)")
    print(f"    Session: {session_name} | Output: {session_dir}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % step == 0:
            idx = existing + saved
            img_name = f"{session_name}_{idx:05d}.jpg"
            img_path = os.path.join(session_dir, img_name)
            cv2.imwrite(img_path, frame)
            saved += 1

        frame_idx += 1

    cap.release()
    print(f"    Extracted: {saved} frames")
    return saved


def main():
    args = parse_args()

    # Find videos to process
    videos = []

    if args.video:
        videos = [args.video]
    elif args.videodir:
        videos = sorted(glob.glob(os.path.join(args.videodir, "*.avi")))
    else:
        # Default: search both root raw_video and Stage 01 raw_video
        candidate_dirs = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_video"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01 Camera Stream and Record", "raw_video"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_video"),
        ]
        for cd in candidate_dirs:
            if os.path.isdir(cd):
                found = glob.glob(os.path.join(cd, "*.avi"))
                for v in found:
                    if v not in videos:
                        videos.append(v)
        videos.sort()
        if not videos:
            print("[!] No videos found. Specify --video or --videodir.")
            print(f"    Searched: {candidate_dirs}")
            sys.exit(1)

    print(f"[+] Found {len(videos)} video(s) to process")
    print(f"[+] Extraction interval: {args.interval}s")

    total_saved = 0
    for video in videos:
        session = args.session if args.session else ""
        total_saved += extract_from_video(video, args.outdir, args.interval, session)

    print(f"\n{'=' * 40}")
    print(f"  Total frames extracted: {total_saved}")
    print(f"  Output directory: {args.outdir}")
    print(f"{'=' * 40}")


if __name__ == "__main__":
    main()
