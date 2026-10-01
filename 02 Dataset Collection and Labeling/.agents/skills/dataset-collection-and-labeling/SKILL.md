---
name: dataset-collection-and-labeling
description: Turn recorded video into a clean, correctly split, labeled object detection dataset for a black balloon.
---

# Dataset Collection and Labeling

## Goal
A clean YOLO-format dataset: images plus label files, split into train, val and test with no leakage.

## Rules
1. Extract frames from video at a low rate (1-2 fps). Consecutive frames are near duplicates and add little value.
2. Target size: 500+ labeled positive images to start, plus 15-25% negative images (no balloon, empty label file).
3. Split BY SESSION, not by random frame. Frames from the same session in both train and val inflate accuracy and hide real errors.
   - Example: sessions 1-6 train, session 7 val, session 8 test.
4. Single class: `balloon`.
5. Labeling rules (be consistent):
   - Tight box around the visible balloon body, excluding the string.
   - Partially visible balloon: label the visible part.
   - Not label if less than about 20% is visible or it is unrecognizable.
6. Tools: Roboflow, CVAT or Label Studio. Export in YOLO format.
7. Review 10% of labels manually for mistakes. Bad labels cap accuracy.

## Frame extraction
```python
import cv2, os, sys
video, outdir, every_sec = sys.argv[1], sys.argv[2], 0.7
os.makedirs(outdir, exist_ok=True)
cap = cv2.VideoCapture(video)
fps = cap.get(cv2.CAP_PROP_FPS) or 15
step = max(1, int(fps * every_sec))
i = n = 0
base = os.path.splitext(os.path.basename(video))[0]
while True:
    ok, f = cap.read()
    if not ok: break
    if i % step == 0:
        cv2.imwrite(f"{outdir}/{base}_{n:05d}.jpg", f); n += 1
    i += 1
print("saved", n)
```

## Dataset layout
```
dataset/
  images/train  images/val  images/test
  labels/train  labels/val  labels/test
  data.yaml
```
`data.yaml`:
```yaml
path: dataset
train: images/train
val: images/val
test: images/test
names: {0: balloon}
```

## Hard-example loop
After the first model works, run it on new video, save frames where it is wrong (missed balloon or false detection), label them, add them to train, and retrain. Repeat 2-3 times.

## Done when
- Splits are by session, label quality is spot-checked, and negatives are included.
