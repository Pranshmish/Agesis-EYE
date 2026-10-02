#!/usr/bin/env python3
"""
balloon_tool.py - dataset builder for the black-balloon detector.

Pipeline (run in this order):
  1. dedupe    drop near-identical consecutive frames
  2. prelabel  propose boxes with independent methods (OWLv2, your own YOLO best.pt, optional classical)
               - both agree (IoU >= --agree)  -> auto label (still spot-check it!)
               - otherwise                    -> goes to the review queue
  3. sheet     contact sheets so you can eyeball auto labels (do this BEFORE training)
  4. review    fast OpenCV UI to accept / redraw / mark "no balloon" for the queue
  5. split     session-aware train/val/test + data.yaml (YOLO format)

Install:   pip install opencv-python numpy pillow
Optional:  pip install torch transformers      (enables OWLv2, much better proposals)

Examples:
  python balloon_tool.py dedupe   --src raw_frames --work work --thr 3
  python balloon_tool.py prelabel --work work --owl --model runs/detect/v1/weights/best.pt
  python balloon_tool.py sheet    --work work --which auto --n 48
  python balloon_tool.py review   --work work
  python balloon_tool.py split    --work work --out dataset_v3

Frame names must look like  <session>_<index>.jpg  (e.g. session_01_00042.jpg).
Nothing is trusted blindly: every auto label is either spot-checked or reviewed by you.
"""
import argparse, json, os, random, re, shutil, sys
from pathlib import Path
import cv2
import numpy as np

IMG_EXT = {".jpg", ".jpeg", ".png"}


# ----------------------------------------------------------------- helpers
def list_images(folder):
    return sorted(p for p in Path(folder).rglob("*") if p.suffix.lower() in IMG_EXT and re.match(r".*_\d+\.\w+$", p.name))


def session_of(name):
    m = re.match(r"(.*)_(\d+)\.\w+$", name)
    return m.group(1) if m else "session_unknown"


def frame_index(name):
    m = re.search(r"_(\d+)\.\w+$", name)
    return int(m.group(1)) if m else 0


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def write_label(path, box, w, h):
    """box = [x1,y1,x2,y2] in pixels, or None for a negative (empty file)."""
    if box is None:
        Path(path).write_text("")
        return
    x1, y1, x2, y2 = [float(v) for v in box]
    x1, x2 = sorted((min(max(x1, 0), w), min(max(x2, 0), w)))
    y1, y2 = sorted((min(max(y1, 0), h), min(max(y2, 0), h)))
    if x2 - x1 < 3 or y2 - y1 < 3:
        Path(path).write_text("")
        return
    cx, cy, bw, bh = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h
    Path(path).write_text(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")


def read_label(path, w, h):
    p = Path(path)
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        t = line.split()
        if len(t) == 5:
            cx, cy, bw, bh = [float(v) for v in t[1:]]
            return [(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h]
    return None


def load_json(path, default):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1))


# ----------------------------------------------------------------- 1. dedupe
def cmd_dedupe(a):
    out = Path(a.work) / "images"
    out.mkdir(parents=True, exist_ok=True)
    files = list_images(a.src)
    last, last_sess, kept = None, None, 0
    for f in files:
        sess = session_of(f.name)
        img = cv2.imread(str(f))
        if img is None:
            print("unreadable, skipped:", f.name)
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if g.mean() < a.min_bright:  # nearly black frame
            continue
        t = cv2.resize(g, (40, 30)).astype(np.float32)
        if last is not None and sess == last_sess and np.abs(t - last).mean() < a.thr:
            continue
        shutil.copy(f, out / f.name)
        last, last_sess, kept = t, sess, kept + 1
    print(f"kept {kept} of {len(files)} frames -> {out}")


# ----------------------------------------------------------------- 2. prelabel
def cv_detect(img):
    """Classical proposal: dark-grey, low-saturation, round blob (balloon has a bright specular
    highlight, so fill holes). Weak on purpose: it only has to AGREE with OWLv2, not replace it."""
    h, w = img.shape[:2]
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    sat = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)[..., 1]
    mask = ((gray < 125) & (gray > 12) & (sat < 75)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best, best_s = None, 0.0
    for c in cnts:
        area = cv2.contourArea(c)
        frac = area / (w * h)
        if not (0.01 < frac < 0.5):
            continue
        per = cv2.arcLength(c, True)
        circ = 4 * np.pi * area / (per * per + 1e-6)
        solid = area / (cv2.contourArea(cv2.convexHull(c)) + 1e-6)
        x, y, bw, bh = cv2.boundingRect(c)
        aspect = min(bw, bh) / max(bw, bh)
        touches = x <= 1 or y <= 1 or x + bw >= w - 1 or y + bh >= h - 1
        if circ < 0.6 or solid < 0.9 or aspect < 0.65 or touches:
            continue
        sc = circ * solid * aspect * np.sqrt(frac)
        if sc > best_s:
            best, best_s = [x, y, x + bw, y + bh], sc
    return best


class Owl:
    def __init__(self, device):
        import torch
        from transformers import Owlv2Processor, Owlv2ForObjectDetection
        self.torch = torch
        name = "google/owlv2-base-patch16-ensemble"
        self.proc = Owlv2Processor.from_pretrained(name)
        self.model = Owlv2ForObjectDetection.from_pretrained(name).to(device).eval()
        self.device = device

    def detect(self, img_bgr, thr):
        from PIL import Image
        torch = self.torch
        rgb = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        w, h = rgb.size
        inp = self.proc(text=[["a black balloon"]], images=rgb, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model(**inp)
        s = max(w, h)  # OWLv2 pads to a square, boxes are in padded coordinates
        res = self.proc.post_process_object_detection(
            out, threshold=thr, target_sizes=torch.tensor([[s, s]], device=self.device))[0]
        if len(res["scores"]) == 0:
            return None
        i = int(res["scores"].argmax())
        b = res["boxes"][i].tolist()
        return [max(0, b[0]), max(0, b[1]), min(w, b[2]), min(h, b[3])]


class Yolo:
    def __init__(self, weights):
        from ultralytics import YOLO
        self.m = YOLO(weights)

    def detect(self, img_bgr, conf):
        r = self.m(img_bgr, conf=conf, verbose=False)[0]
        if len(r.boxes) == 0:
            return None
        i = int(r.boxes.conf.argmax())
        return [float(v) for v in r.boxes.xyxy[i].tolist()]


def cmd_prelabel(a):
    """Two or more INDEPENDENT proposers must agree (IoU >= --agree) for an auto label.
    Proposers: --owl (OWLv2 zero-shot), --model best.pt (your own YOLO, bootstrap), --classical (weak).
    With fewer than two proposers nothing is auto-accepted: everything goes to review."""
    work = Path(a.work)
    imgs, labs = work / "images", work / "labels"
    labs.mkdir(exist_ok=True)
    detectors = {}
    if a.owl:
        try:
            import torch
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            print("loading OWLv2 on", dev)
            o = Owl(dev)
            detectors["owl"] = lambda im: o.detect(im, a.owl_thr)
        except Exception as e:
            print("OWLv2 unavailable (%s)" % e)
    if a.model:
        try:
            y = Yolo(a.model)
            detectors["yolo"] = lambda im: y.detect(im, a.model_conf)
        except Exception as e:
            print("YOLO model unavailable (%s)" % e)
    if a.classical:
        detectors["classical"] = cv_detect
    if len(detectors) < 2:
        print(f"only {len(detectors)} proposer(s) available -> nothing will be auto-accepted; "
              "use `review --all` (or train a first model on ~100 hand labels and pass --model).")
    props = load_json(work / "proposals.json", {})
    files = list_images(imgs)
    n_auto = 0
    for i, f in enumerate(files):
        if f.name in props:
            continue
        img = cv2.imread(str(f))
        h, w = img.shape[:2]
        boxes = {k: fn(img) for k, fn in detectors.items()}
        found = [(k, b) for k, b in boxes.items() if b]
        status, final = "review", (found[0][1] if found else None)
        for x in range(len(found)):
            for y in range(x + 1, len(found)):
                if iou(found[x][1], found[y][1]) >= a.agree:
                    status = "auto"
                    final = [(p + q) / 2 for p, q in zip(found[x][1], found[y][1])]
        if status == "auto":
            write_label(labs / (f.stem + ".txt"), final, w, h)
            n_auto += 1
        props[f.name] = {"status": status, "box": final, "proposers": boxes}
        if (i + 1) % 50 == 0:
            save_json(work / "proposals.json", props)
            print(f"{i + 1}/{len(files)}")
    save_json(work / "proposals.json", props)
    total = len(props)
    print(f"auto-accepted {n_auto}/{total}; review queue {total - n_auto}")
    print("NEXT: run `sheet --which auto` and look at the grids before trusting auto labels.")


# ----------------------------------------------------------------- 3. sheet
def draw_box(img, box, color=(0, 255, 0)):
    if box:
        cv2.rectangle(img, tuple(int(v) for v in box[:2]), tuple(int(v) for v in box[2:]), color, 2)


def cmd_sheet(a):
    work = Path(a.work)
    props = load_json(work / "proposals.json", {})
    state = load_json(work / "review_state.json", {})
    if a.which == "auto":
        names = [n for n, p in props.items() if p["status"] == "auto"]
    else:  # everything that currently has a label file, incl. reviewed
        names = [n for n in props if (work / "labels" / (Path(n).stem + ".txt")).exists()]
    random.seed(0)
    random.shuffle(names)
    names = names[: a.n]
    out = work / "sheets"
    out.mkdir(exist_ok=True)
    cols, rows, W, H = 6, 4, 320, 240
    per = cols * rows
    for s in range(0, len(names), per):
        sheet = np.zeros((H * rows, W * cols, 3), np.uint8)
        for j, n in enumerate(names[s:s + per]):
            img = cv2.resize(cv2.imread(str(work / "images" / n)), (W, H))
            box = read_label(work / "labels" / (Path(n).stem + ".txt"), W, H)
            draw_box(img, box)
            cv2.putText(img, n[-9:-4], (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            sheet[(j // cols) * H:(j // cols + 1) * H, (j % cols) * W:(j % cols + 1) * W] = img
        p = out / f"{a.which}_{s // per:03d}.jpg"
        cv2.imwrite(str(p), sheet)
        print("wrote", p)
    print("Rule: if more than 5% of boxes in a sheet miss the balloon, REJECT auto labels and "
          "send everything to review (`review --all`).")


# ----------------------------------------------------------------- 4. review
def cmd_review(a):
    work = Path(a.work)
    props = load_json(work / "proposals.json", {})
    state_p = work / "review_state.json"
    state = load_json(state_p, {})
    labs = work / "labels"
    labs.mkdir(exist_ok=True)
    queue = [n for n, p in props.items() if (a.all or p["status"] == "review") and n not in state]
    print(f"{len(queue)} frames to review.  Keys: [Enter/Space]=accept box  [drag mouse]=draw new box  "
          "[n]=no balloon  [c]=clear box  [s]=skip  [b]=back  [q]=quit")
    S = 3  # display scale
    win = "review"
    cur = {"box": None, "drag": None}

    def mouse(ev, x, y, flags, _):
        if ev == cv2.EVENT_LBUTTONDOWN:
            cur["drag"] = (x, y)
        elif ev == cv2.EVENT_MOUSEMOVE and cur["drag"]:
            x0, y0 = cur["drag"]
            cur["box"] = [min(x0, x) / S, min(y0, y) / S, max(x0, x) / S, max(y0, y) / S]
        elif ev == cv2.EVENT_LBUTTONUP and cur["drag"]:
            x0, y0 = cur["drag"]
            cur["drag"] = None
            cur["box"] = [min(x0, x) / S, min(y0, y) / S, max(x0, x) / S, max(y0, y) / S]

    cv2.namedWindow(win)
    cv2.setMouseCallback(win, mouse)
    i = 0
    while 0 <= i < len(queue):
        n = queue[i]
        img = cv2.imread(str(work / "images" / n))
        h, w = img.shape[:2]
        cur["box"] = props[n].get("box")
        cur["drag"] = None
        while True:
            view = cv2.resize(img, (w * S, h * S), interpolation=cv2.INTER_CUBIC)
            if cur["box"]:
                draw_box(view, [v * S for v in cur["box"]])
            cv2.putText(view, f"{i + 1}/{len(queue)} {n}", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imshow(win, view)
            k = cv2.waitKey(20) & 0xFF
            if k in (13, 32):  # accept
                if cur["box"] is None:
                    print("no box to accept - draw one or press n")
                    continue
                write_label(labs / (Path(n).stem + ".txt"), cur["box"], w, h)
                state[n] = "box"
                i += 1
                break
            if k == ord("n"):
                write_label(labs / (Path(n).stem + ".txt"), None, w, h)
                state[n] = "neg"
                i += 1
                break
            if k == ord("c"):
                cur["box"] = None
            if k == ord("s"):
                state[n] = "skip"
                i += 1
                break
            if k == ord("b") and i > 0:
                i -= 1
                state.pop(queue[i], None)
                break
            if k == ord("q"):
                save_json(state_p, state)
                cv2.destroyAllWindows()
                print("saved. re-run `review` to continue.")
                return
        save_json(state_p, state)
    cv2.destroyAllWindows()
    print("review done.")


# ----------------------------------------------------------------- 5. split
def cmd_split(a):
    work, out = Path(a.work), Path(a.out)
    props = load_json(work / "proposals.json", {})
    state = load_json(work / "review_state.json", {})
    ok = [n for n, p in props.items()
          if state.get(n) in ("box", "neg") or (p["status"] == "auto" and state.get(n) != "skip")]
    pending = [n for n, p in props.items() if p["status"] == "review" and n not in state]
    if pending:
        print(f"WARNING: {len(pending)} frames in the review queue are unlabeled and excluded.")
    by_sess = {}
    for n in ok:
        by_sess.setdefault(session_of(n), []).append(n)
    sess = sorted(by_sess)
    split = {"train": [], "val": [], "test": []}
    if len(sess) >= 3:  # whole sessions -> honest validation
        random.seed(0)
        random.shuffle(sess)
        nt = max(1, round(len(sess) * 0.15))
        nv = max(1, round(len(sess) * 0.15))
        for s in sess[:nt]: split["test"] += by_sess[s]
        for s in sess[nt:nt + nv]: split["val"] += by_sess[s]
        for s in sess[nt + nv:]: split["train"] += by_sess[s]
    else:
        print(f"WARNING: only {len(sess)} session(s). Using contiguous blocks with a 15-frame gap. "
              "Val/test then share scene+lighting with train, so their scores are optimistic. "
              "Record more sessions.")
        for s in sess:
            names = sorted(by_sess[s], key=frame_index)
            n = len(names)
            a1, a2 = int(n * 0.7), int(n * 0.85)
            split["train"] += names[:max(0, a1 - 15)]
            split["val"] += names[a1:max(a1, a2 - 15)]
            split["test"] += names[a2:]
    for sp, names in split.items():
        (out / "images" / sp).mkdir(parents=True, exist_ok=True)
        (out / "labels" / sp).mkdir(parents=True, exist_ok=True)
        pos = 0
        for n in names:
            shutil.copy(work / "images" / n, out / "images" / sp / n)
            lp = work / "labels" / (Path(n).stem + ".txt")
            txt = lp.read_text() if lp.exists() else ""
            pos += bool(txt.strip())
            (out / "labels" / sp / (Path(n).stem + ".txt")).write_text(txt)
        print(f"{sp}: {len(names)} images, {pos} positive, {len(names) - pos} negative")
    (out / "data.yaml").write_text("path: .\ntrain: images/train\nval: images/val\ntest: images/test\n"
                                   "names:\n  0: balloon\nnc: 1\n")
    print("wrote", out / "data.yaml")
    print("Test split should have 100+ positives before you trust its numbers.")


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("dedupe"); p.add_argument("--src", required=True); p.add_argument("--work", default="work")
    p.add_argument("--thr", type=float, default=3.0, help="mean abs diff (0-255) below which a frame is a duplicate")
    p.add_argument("--min-bright", type=float, default=15, help="drop frames darker than this")
    p.set_defaults(fn=cmd_dedupe)
    p = sub.add_parser("prelabel"); p.add_argument("--work", default="work")
    p.add_argument("--owl", action="store_true", help="use OWLv2 (needs torch+transformers, downloads ~600MB)")
    p.add_argument("--owl-thr", type=float, default=0.15); p.add_argument("--agree", type=float, default=0.6)
    p.add_argument("--model", help="your trained YOLO weights (best.pt) as a second proposer")
    p.add_argument("--model-conf", type=float, default=0.4)
    p.add_argument("--classical", action="store_true", help="add the weak dark-blob proposer (off by default)")
    p.set_defaults(fn=cmd_prelabel)
    p = sub.add_parser("sheet"); p.add_argument("--work", default="work")
    p.add_argument("--which", choices=["auto", "labels"], default="auto"); p.add_argument("--n", type=int, default=48)
    p.set_defaults(fn=cmd_sheet)
    p = sub.add_parser("review"); p.add_argument("--work", default="work")
    p.add_argument("--all", action="store_true", help="review every frame, not just the disagreement queue")
    p.set_defaults(fn=cmd_review)
    p = sub.add_parser("split"); p.add_argument("--work", default="work"); p.add_argument("--out", default="dataset_v3")
    p.set_defaults(fn=cmd_split)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
