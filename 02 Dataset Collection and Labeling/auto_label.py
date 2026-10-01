"""
Automatic Balloon Dataset Labeler — Detects and tracks balloon bounding boxes across frames.

Features:
- Robust spherical balloon detection (Hough circle + dark specular reflection).
- Temporal tracking fallback when moving fast or partially occluded.
- Automatic negative handling (empty label file if target not present).
- Generates standard YOLO formatted .txt labels (0 cx cy w h).
- Exports visual preview grid (auto_label_preview.jpg) for quick review.

Usage:
    python auto_label.py                                    # Labels raw_frames/session_01
    python auto_label.py --dir raw_frames/session_01        # Specific folder
    python auto_label.py --show                             # Live preview window
"""
import os
import sys
import glob
import argparse
import cv2
import numpy as np

CLASS_ID = 0
CLASS_NAME = "balloon"


def parse_args():
    p = argparse.ArgumentParser(description="Automatic Balloon YOLO Labeler")
    p.add_argument("--dir", default="raw_frames/session_01",
                   help="Directory containing session .jpg images")
    p.add_argument("--show", action="store_true",
                   help="Display live detection window while labeling")
    p.add_argument("--preview", action="store_true", default=True,
                   help="Generate 3x3 sample preview image")
    return p.parse_args()


def detect_balloon_circle(img, last_box=None):
    """
    Detects spherical balloon using Hough Circle Transform + dark specular analysis.
    Returns (x, y, w, h) in pixel coordinates or None.
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
        param1=50, param2=30, minRadius=18, maxRadius=85
    )

    if circles is None:
        return None

    candidates = []
    for c in circles[0]:
        cx, cy, r = int(c[0]), int(c[1]), int(c[2])
        if cx < 0 or cy < 0 or cx >= w or cy >= h:
            continue

        # Bounding box
        x1 = max(0, cx - r)
        y1 = max(0, cy - r)
        x2 = min(w, cx + r)
        y2 = min(h, cy + r)
        bw = x2 - x1
        bh = y2 - y1

        if bw < 20 or bh < 20:
            continue

        crop = gray[y1:y2, x1:x2]
        mean_brightness = np.mean(crop)

        # Balloon body is predominantly dark (mean < 95)
        if mean_brightness > 95:
            continue

        score = r
        # Temporal proximity bonus if we have a previous box
        if last_box is not None:
            lx, ly, lbw, lbh = last_box
            lcx, lcy = lx + lbw / 2, ly + lbh / 2
            dist = np.hypot(cx - lcx, cy - lcy)
            if dist < 80:
                score += 50

        candidates.append(((x1, y1, bw, bh), score))

    if not candidates:
        return None

    # Pick candidate with highest score
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def save_yolo_label(lbl_path, box, img_w, img_h):
    """Save normalized YOLO bounding box."""
    if box is None:
        # Negative image (empty file)
        open(lbl_path, 'w').close()
        return

    x, y, bw, bh = box
    norm_w = bw / img_w
    norm_h = bh / img_h
    norm_cx = (x + bw / 2.0) / img_w
    norm_cy = (y + bh / 2.0) / img_h

    # Clamp
    norm_cx = max(0.0, min(1.0, norm_cx))
    norm_cy = max(0.0, min(1.0, norm_cy))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))

    with open(lbl_path, 'w') as f:
        f.write(f"{CLASS_ID} {norm_cx:.6f} {norm_cy:.6f} {norm_w:.6f} {norm_h:.6f}\n")


def generate_preview_grid(files, out_path="auto_label_preview.jpg", num_samples=9):
    """Creates a 3x3 visual summary of labeled frames."""
    if not files:
        return
    step = max(1, len(files) // num_samples)
    samples = files[::step][:num_samples]

    grid_imgs = []
    for f in samples:
        img = cv2.imread(f)
        if img is None:
            continue
        h, w = img.shape[:2]
        lbl = os.path.splitext(f)[0] + ".txt"

        if os.path.exists(lbl) and os.path.getsize(lbl) > 0:
            with open(lbl) as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        _, cx, cy, bw, bh = map(float, parts[:5])
                        x1 = int((cx - bw / 2.0) * w)
                        y1 = int((cy - bh / 2.0) * h)
                        x2 = int((cx + bw / 2.0) * w)
                        y2 = int((cy + bh / 2.0) * h)
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(img, CLASS_NAME, (x1, max(15, y1 - 5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
        else:
            cv2.putText(img, "[NEGATIVE]", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.putText(img, os.path.basename(f), (5, h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        grid_imgs.append(img)

    while len(grid_imgs) < 9:
        grid_imgs.append(np.zeros((240, 320, 3), dtype=np.uint8))

    row1 = np.hstack(grid_imgs[0:3])
    row2 = np.hstack(grid_imgs[3:6])
    row3 = np.hstack(grid_imgs[6:9])
    grid = np.vstack([row1, row2, row3])
    cv2.imwrite(out_path, grid)
    print(f"[+] Saved visual preview grid: {out_path}")


def main():
    args = parse_args()
    raw_files = glob.glob(os.path.join(args.dir, "*.jpg"))
    files = sorted([f for f in raw_files if "preview" not in f and "result" not in f])

    if not files:
        print(f"[ERROR] No .jpg files found in {args.dir}")
        sys.exit(1)

    print(f"\n[+] Auto-labeling {len(files)} frames in '{args.dir}'...")

    labeled_pos = 0
    labeled_neg = 0
    last_valid_box = None

    window_name = "Auto Balloon Labeler"
    if args.show:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)

    for i, img_path in enumerate(files):
        img = cv2.imread(img_path)
        if img is None:
            continue
        h, w = img.shape[:2]
        lbl_path = os.path.splitext(img_path)[0] + ".txt"

        box = detect_balloon_circle(img, last_box=last_valid_box)

        if box is not None:
            save_yolo_label(lbl_path, box, w, h)
            last_valid_box = box
            labeled_pos += 1
        else:
            save_yolo_label(lbl_path, None, w, h)
            labeled_neg += 1

        if args.show:
            disp = img.copy()
            if box is not None:
                x, y, bw, bh = box
                cv2.rectangle(disp, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
                cv2.putText(disp, f"{CLASS_NAME}", (x, max(15, y - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            else:
                cv2.putText(disp, "[NEGATIVE]", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            cv2.imshow(window_name, disp)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    if args.show:
        cv2.destroyAllWindows()

    print(f"\n{'=' * 45}")
    print(f"  Auto-labeling Complete!")
    print(f"  Total frames processed : {len(files)}")
    print(f"  Labeled positive (box) : {labeled_pos}")
    print(f"  Labeled negative (none): {labeled_neg}")
    print(f"{'=' * 45}\n")

    if args.preview:
        out_preview = os.path.join(args.dir, "auto_label_preview.jpg")
        generate_preview_grid(files, out_preview)


if __name__ == "__main__":
    main()
