"""
Lightweight Interactive YOLO Labeling Tool — Quick annotation without external tools.

Usage:
    python label_helper.py                               # Labels frames in raw_frames/
    python label_helper.py --dir raw_frames/session_01   # Specific session folder
    python label_helper.py --dir dataset/images/train    # Direct dataset folder

Controls:
    Mouse Drag    : Draw bounding box around balloon
    S             : Save annotations to YOLO .txt file
    SPACE / D     : Next image (auto-saves if box drawn)
    A             : Previous image
    C             : Clear current boxes
    X             : Mark as negative (no balloon, saves empty label file)
    ESC / Q       : Exit
"""
import os
import sys
import glob
import argparse
import cv2

# Class 0: balloon
CLASS_ID = 0
CLASS_NAME = "balloon"


class LabelTool:
    def __init__(self, image_paths, out_dir=None):
        self.image_paths = image_paths
        self.out_dir = out_dir
        self.idx = 0
        self.boxes = []       # [(x1, y1, x2, y2)] in pixel coords
        self.drawing = False
        self.pt_start = (0, 0)
        self.pt_current = (0, 0)
        self.cur_img = None
        self.window_name = "YOLO Annotation Helper (Class 0: balloon)"

    def get_label_path(self, img_path):
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        if self.out_dir:
            return os.path.join(self.out_dir, f"{base_name}.txt")
        return os.path.splitext(img_path)[0] + ".txt"

    def load_existing_labels(self, img_path, img_w, img_h):
        lbl_path = self.get_label_path(img_path)
        boxes = []
        if os.path.exists(lbl_path):
            with open(lbl_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        _, cx, cy, bw, bh = map(float, parts[:5])
                        x1 = int((cx - bw / 2.0) * img_w)
                        y1 = int((cy - bh / 2.0) * img_h)
                        x2 = int((cx + bw / 2.0) * img_w)
                        y2 = int((cy + bh / 2.0) * img_h)
                        boxes.append((x1, y1, x2, y2))
        return boxes

    def save_labels(self, img_path, img_w, img_h):
        lbl_path = self.get_label_path(img_path)
        os.makedirs(os.path.dirname(os.path.abspath(lbl_path)), exist_ok=True)
        with open(lbl_path, "w") as f:
            for x1, y1, x2, y2 in self.boxes:
                xmin, xmax = min(x1, x2), max(x1, x2)
                ymin, ymax = min(y1, y2), max(y1, y2)
                bw = (xmax - xmin) / img_w
                bh = (ymax - ymin) / img_h
                cx = (xmin + xmax) / (2.0 * img_w)
                cy = (ymin + ymax) / (2.0 * img_h)
                # Clamp between 0 and 1
                cx = max(0.0, min(1.0, cx))
                cy = max(0.0, min(1.0, cy))
                bw = max(0.0, min(1.0, bw))
                bh = max(0.0, min(1.0, bh))
                f.write(f"{CLASS_ID} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
        print(f"[Saved] {len(self.boxes)} box(es) -> {os.path.basename(lbl_path)}")

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.pt_start = (x, y)
            self.pt_current = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.pt_current = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                x1, y1 = self.pt_start
                x2, y2 = x, y
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    self.boxes.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def run(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 600)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        total = len(self.image_paths)
        if total == 0:
            print("No images found to label.")
            return

        while 0 <= self.idx < total:
            img_path = self.image_paths[self.idx]
            self.cur_img = cv2.imread(img_path)
            if self.cur_img is None:
                self.idx += 1
                continue

            h, w = self.cur_img.shape[:2]
            self.boxes = self.load_existing_labels(img_path, w, h)

            while True:
                display = self.cur_img.copy()

                # Draw existing boxes
                for (x1, y1, x2, y2) in self.boxes:
                    cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display, CLASS_NAME, (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # Draw box currently being dragged
                if self.drawing:
                    cv2.rectangle(display, self.pt_start, self.pt_current, (0, 165, 255), 2)

                # Status overlay
                lbl_path = self.get_label_path(img_path)
                has_label = os.path.exists(lbl_path)
                status_color = (0, 255, 0) if has_label else (0, 0, 255)
                status_str = f"[{self.idx + 1}/{total}] {os.path.basename(img_path)} | Boxes: {len(self.boxes)}"
                cv2.putText(display, status_str, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)

                guide = "Drag: Box | S/Space: Next+Save | A: Prev | C: Clear | X: Negative | Q: Exit"
                cv2.putText(display, guide, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

                cv2.imshow(self.window_name, display)
                key = cv2.waitKey(20) & 0xFF

                if key in (ord('q'), 27):  # Q or ESC
                    cv2.destroyAllWindows()
                    return
                elif key in (ord('s'), 32, ord('d')):  # S, Space, D -> Next + Save
                    self.save_labels(img_path, w, h)
                    self.idx += 1
                    break
                elif key == ord('a'):  # Prev
                    self.save_labels(img_path, w, h)
                    self.idx = max(0, self.idx - 1)
                    break
                elif key == ord('c'):  # Clear boxes
                    self.boxes = []
                elif key == ord('x'):  # Mark negative
                    self.boxes = []
                    self.save_labels(img_path, w, h)
                    self.idx += 1
                    break

        cv2.destroyAllWindows()
        print("\n[+] Annotation session finished!")


def main():
    p = argparse.ArgumentParser(description="Lightweight YOLO Annotation Tool")
    p.add_argument("--dir", default="", help="Directory containing images")
    p.add_argument("--outdir", default="", help="Optional output dir for label files")
    args = p.parse_args()

    search_dirs = [args.dir] if args.dir else [
        "raw_frames",
        os.path.join(os.path.dirname(__file__), "raw_frames"),
        os.path.join(os.path.dirname(__file__), "dataset", "images", "train"),
    ]

    images = []
    for d in search_dirs:
        if d and os.path.isdir(d):
            imgs = glob.glob(os.path.join(d, "**", "*.jpg"), recursive=True)
            if imgs:
                images = sorted(imgs)
                break

    if not images:
        print("[!] No .jpg images found in search paths.")
        print("    Specify directory with: python label_helper.py --dir <path/to/images>")
        sys.exit(1)

    print(f"[+] Loaded {len(images)} images to label.")
    tool = LabelTool(images, out_dir=args.outdir if args.outdir else None)
    tool.run()


if __name__ == "__main__":
    main()
