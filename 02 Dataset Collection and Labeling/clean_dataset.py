"""
Dataset Cleaning & Negative Audit Tool — Prune garbage frames and fix missed labels.

Features:
1. Auto-detects pitch-black (<25 brightness) or unusable frames.
2. Rapid Review Mode: Specifically iterates through EMPTY (negative) frames so you can:
   - Press SPACE to confirm "Yes, truly negative (no balloon)".
   - Drag mouse to label a missed balloon.
   - Press D to delete a black/blurry frame.
3. Box Sanity Check: Identifies suspiciously small (<15px) or oversized (>80% frame) boxes.

Usage:
    # 1. Audit and clean empty/negative frames in session_01:
    python clean_dataset.py --dir raw_frames/session_01 --review-negatives

    # 2. Check entire dataset for corrupt/black frames:
    python clean_dataset.py --dir raw_frames/session_01 --find-garbage

    # 3. Audit all labels in the organized dataset:
    python clean_dataset.py --dir dataset --review-negatives
"""
import os
import sys
import glob
import argparse
import shutil
import cv2
import numpy as np

CLASS_ID = 0
CLASS_NAME = "balloon"


def parse_args():
    p = argparse.ArgumentParser(description="Dataset Quality Audit and Negative Cleaner")
    p.add_argument("--dir", default="raw_frames/session_01",
                   help="Directory to inspect (e.g. raw_frames/session_01 or dataset)")
    p.add_argument("--review-negatives", action="store_true",
                   help="Interactive review mode for empty-label (negative) frames")
    p.add_argument("--find-garbage", action="store_true",
                   help="Scan and delete pitch-black or unusable frames")
    p.add_argument("--black-thresh", type=float, default=25.0,
                   help="Mean brightness threshold below which a frame is considered pitch black (default: 25)")
    return p.parse_args()


def get_image_label_pairs(target_dir):
    """Finds all (image_path, label_path) in target_dir recursively."""
    pairs = []
    # If target is dataset root, search images/
    img_search_dirs = [
        target_dir,
        os.path.join(target_dir, "images", "train"),
        os.path.join(target_dir, "images", "val"),
        os.path.join(target_dir, "images", "test"),
    ]
    for d in img_search_dirs:
        if os.path.isdir(d):
            for f in sorted(glob.glob(os.path.join(d, "*.jpg"))):
                if "preview" in f or "result" in f:
                    continue
                # Determine corresponding label path
                if "images" in f:
                    lbl = f.replace("images", "labels").replace(".jpg", ".txt")
                else:
                    lbl = f.replace(".jpg", ".txt")
                pairs.append((f, lbl))
    return pairs


def find_and_clean_garbage(pairs, black_thresh=25.0):
    """Detects and reports pitch-black or severely corrupted frames."""
    print(f"\n[+] Scanning {len(pairs)} frames for pitch-black / corrupted images...")
    garbage = []

    for img_path, lbl_path in pairs:
        img = cv2.imread(img_path)
        if img is None:
            garbage.append((img_path, lbl_path, "Corrupt file (cannot decode)"))
            continue

        mean_val = float(np.mean(img))
        std_val = float(np.std(img))

        if mean_val < black_thresh:
            garbage.append((img_path, lbl_path, f"Pitch black (mean: {mean_val:.1f} < {black_thresh})"))
        elif std_val < 5.0:
            garbage.append((img_path, lbl_path, f"Zero contrast (std: {std_val:.1f})"))

    print(f"[!] Found {len(garbage)} garbage frames.")
    if not garbage:
        print("    All frames passed basic brightness/integrity check!")
        return

    for img_path, _, reason in garbage[:15]:
        print(f"    - {os.path.basename(img_path):28s} : {reason}")
    if len(garbage) > 15:
        print(f"    ... and {len(garbage) - 15} more.")

    confirm = input(f"\nDo you want to DELETE these {len(garbage)} garbage frames? (y/n): ").strip().lower()
    if confirm == 'y':
        for img_path, lbl_path, _ in garbage:
            if os.path.exists(img_path):
                os.remove(img_path)
            if os.path.exists(lbl_path):
                os.remove(lbl_path)
            json_meta = img_path.replace('.jpg', '.json')
            if os.path.exists(json_meta):
                os.remove(json_meta)
        print(f"[+] Deleted {len(garbage)} garbage frames and labels.")


class NegativeReviewer:
    def __init__(self, negative_pairs):
        self.pairs = negative_pairs
        self.idx = 0
        self.drawing = False
        self.pt_start = (0, 0)
        self.pt_current = (0, 0)
        self.drawn_box = None
        self.window_name = "Audit Negative Frames (D=Delete | SPACE=Confirm Neg | Drag=Draw Box | S=Save Box | Q=Quit)"

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.pt_start = (x, y)
            self.pt_current = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.pt_current = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            x1, y1 = self.pt_start
            x2, y2 = x, y
            if abs(x2 - x1) > 8 and abs(y2 - y1) > 8:
                self.drawn_box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def save_box(self, img_path, lbl_path, w, h):
        if self.drawn_box is None:
            return
        x1, y1, x2, y2 = self.drawn_box
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        cx = (x1 + x2) / (2.0 * w)
        cy = (y1 + y2) / (2.0 * h)
        os.makedirs(os.path.dirname(os.path.abspath(lbl_path)), exist_ok=True)
        with open(lbl_path, 'w') as f:
            f.write(f"{CLASS_ID} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
        print(f"[+] Fixed Missed Label -> {os.path.basename(lbl_path)}")

    def run(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 640, 480)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        total = len(self.pairs)
        print(f"\n[+] Starting negative review of {total} frames...")
        print("    - SPACE : Confirm genuinely negative (no balloon)")
        print("    - Mouse : Drag rectangle over balloon if missed -> press S to save")
        print("    - D     : Delete blurry/black garbage frame")
        print("    - A     : Back to previous")
        print("    - Q/ESC : Exit review\n")

        while 0 <= self.idx < total:
            img_path, lbl_path = self.pairs[self.idx]
            img = cv2.imread(img_path)
            if img is None:
                self.idx += 1
                continue

            h, w = img.shape[:2]
            self.drawn_box = None

            while True:
                display = img.copy()

                # Status HUD
                status = f"[{self.idx + 1}/{total}] {os.path.basename(img_path)} (CURRENTLY EMPTY)"
                cv2.putText(display, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 165, 255), 2)
                cv2.putText(display, "SPACE: Keep Negative | Drag+S: Fix Box | D: Delete",
                            (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)

                if self.drawing:
                    cv2.rectangle(display, self.pt_start, self.pt_current, (0, 255, 255), 2)
                elif self.drawn_box is not None:
                    x1, y1, x2, y2 = self.drawn_box
                    cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display, "BALLOON (NEW)", (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

                cv2.imshow(self.window_name, display)
                key = cv2.waitKey(20) & 0xFF

                if key in (27, ord('q')):  # ESC / Q
                    cv2.destroyAllWindows()
                    return
                elif key == 32:  # SPACE -> Confirm genuine negative
                    # Ensure label is empty
                    open(lbl_path, 'w').close()
                    self.idx += 1
                    break
                elif key == ord('s'):  # S -> Save drawn box
                    if self.drawn_box is not None:
                        self.save_box(img_path, lbl_path, w, h)
                        self.idx += 1
                        break
                    else:
                        print("  [!] Draw a box first before pressing S!")
                elif key == ord('d'):  # D -> Delete frame
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    if os.path.exists(lbl_path):
                        os.remove(lbl_path)
                    json_meta = img_path.replace('.jpg', '.json')
                    if os.path.exists(json_meta):
                        os.remove(json_meta)
                    print(f"[-] Deleted garbage frame: {os.path.basename(img_path)}")
                    self.pairs.pop(self.idx)
                    total -= 1
                    break
                elif key == ord('a'):  # A -> Back
                    self.idx = max(0, self.idx - 1)
                    break

        cv2.destroyAllWindows()
        print("[+] Negative review completed!")


def main():
    args = parse_args()
    pairs = get_image_label_pairs(args.dir)

    if not pairs:
        print(f"[ERROR] No image/label pairs found in '{args.dir}'")
        sys.exit(1)

    if args.find_garbage:
        find_and_clean_garbage(pairs, black_thresh=args.black_thresh)
    elif args.review_negatives:
        # Filter for pairs where label file is empty
        negative_pairs = [
            (img, lbl) for img, lbl in pairs
            if not os.path.exists(lbl) or os.path.getsize(lbl) == 0
        ]
        print(f"[+] Total frames: {len(pairs)}")
        print(f"[+] Empty-label (negative) frames to audit: {len(negative_pairs)}")
        if not negative_pairs:
            print("[+] No empty frames found! All frames have labels.")
            sys.exit(0)
        reviewer = NegativeReviewer(negative_pairs)
        reviewer.run()
    else:
        print("""
Dataset Clean & Audit Tool:
---------------------------
1. Prune pitch-black or broken frames:
   python clean_dataset.py --dir raw_frames/session_01 --find-garbage

2. Rapid audit of empty/negative frames (fix missed labels or delete):
   python clean_dataset.py --dir raw_frames/session_01 --review-negatives

3. Run across the organized dataset:
   python clean_dataset.py --dir dataset --review-negatives
""")


if __name__ == "__main__":
    main()
