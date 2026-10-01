"""
Organize Dataset — Build YOLO-format dataset from raw_frames/ sessions.

Usage:
    python organize_dataset.py                                     # Interactive
    python organize_dataset.py --train s1,s2,s3 --val s4 --test s5 # Explicit split
    python organize_dataset.py --auto                              # Auto 70/20/10 split

Creates the standard YOLO directory structure:
    dataset/
        images/train/  images/val/  images/test/
        labels/train/  labels/val/  labels/test/
        data.yaml
"""
import os
import sys
import shutil
import argparse
try:
    import yaml
except ImportError:
    yaml = None


def parse_args():
    p = argparse.ArgumentParser(description="Organize frames into YOLO dataset layout")
    p.add_argument("--indir", default="raw_frames", help="Input directory with session subdirs")
    p.add_argument("--outdir", default="dataset", help="Output dataset directory")
    p.add_argument("--train", type=str, default="", help="Comma-separated session names for train split")
    p.add_argument("--val", type=str, default="", help="Comma-separated session names for val split")
    p.add_argument("--test", type=str, default="", help="Comma-separated session names for test split")
    p.add_argument("--auto", action="store_true", help="Auto-split: approx 70%% train, 20%% val, 10%% test by session")
    p.add_argument("--labelsdir", default="labels", help="Directory with YOLO label .txt files (if labeled separately)")
    return p.parse_args()


def find_sessions(indir):
    """Find all session directories in the input folder."""
    sessions = []
    if not os.path.isdir(indir):
        return sessions
    for name in sorted(os.listdir(indir)):
        path = os.path.join(indir, name)
        if os.path.isdir(path):
            jpgs = [f for f in os.listdir(path) if f.endswith('.jpg')]
            if jpgs:
                sessions.append((name, len(jpgs)))
    return sessions


def copy_session(session_name, indir, outdir, split, labelsdir):
    """Copy a session's images and labels into the dataset split."""
    src_dir = os.path.join(indir, session_name)
    img_dst = os.path.join(outdir, "images", split)
    lbl_dst = os.path.join(outdir, "labels", split)
    os.makedirs(img_dst, exist_ok=True)
    os.makedirs(lbl_dst, exist_ok=True)

    copied = 0
    for f in sorted(os.listdir(src_dir)):
        if not f.endswith('.jpg'):
            continue

        # Copy image
        shutil.copy2(os.path.join(src_dir, f), os.path.join(img_dst, f))

        # Look for label file
        label_name = f.replace('.jpg', '.txt')
        label_found = False

        # Check multiple possible label locations
        for lbl_src in [
            os.path.join(src_dir, label_name),           # Same dir as image
            os.path.join(labelsdir, session_name, label_name),  # labels/session/
            os.path.join(labelsdir, label_name),          # labels/
        ]:
            if os.path.exists(lbl_src):
                shutil.copy2(lbl_src, os.path.join(lbl_dst, label_name))
                label_found = True
                break

        # Check if this is a negative frame (from metadata)
        meta_path = os.path.join(src_dir, f.replace('.jpg', '.json'))
        if not label_found and os.path.exists(meta_path):
            import json
            try:
                with open(meta_path) as mf:
                    meta = json.load(mf)
                    if meta.get("negative", False):
                        # Create empty label file for negative
                        open(os.path.join(lbl_dst, label_name), 'w').close()
                        label_found = True
            except Exception:
                pass

        if not label_found:
            # Create empty label (unlabeled = negative by default)
            open(os.path.join(lbl_dst, label_name), 'w').close()

        copied += 1

    return copied


def create_data_yaml(outdir, class_names=None):
    """Create YOLO data.yaml file."""
    if class_names is None:
        class_names = {0: "balloon"}

    data = {
        "path": os.path.abspath(outdir),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": class_names,
        "nc": len(class_names),
    }

    yaml_path = os.path.join(outdir, "data.yaml")
    if yaml is not None:
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        with open(yaml_path, 'w') as f:
            f.write(f"path: {os.path.abspath(outdir).replace(os.sep, '/')}\n")
            f.write("train: images/train\n")
            f.write("val: images/val\n")
            f.write("test: images/test\n")
            f.write(f"nc: {len(class_names)}\n")
            f.write("names:\n")
            for k, v in class_names.items():
                f.write(f"  {k}: {v}\n")

    return yaml_path


def main():
    args = parse_args()

    sessions = find_sessions(args.indir)
    if not sessions:
        print(f"[ERROR] No sessions found in '{args.indir}/'")
        print(f"  Run collect_live.py or extract_frames.py first to create sessions.")
        sys.exit(1)

    print(f"\n[+] Found {len(sessions)} session(s) in '{args.indir}':")
    total_frames = 0
    for name, count in sessions:
        print(f"    {name:30s} → {count} frames")
        total_frames += count
    print(f"    {'TOTAL':30s} → {total_frames} frames\n")

    # Determine splits
    train_sessions = []
    val_sessions = []
    test_sessions = []

    if args.train:
        train_sessions = [s.strip() for s in args.train.split(',')]
        val_sessions = [s.strip() for s in args.val.split(',')] if args.val else []
        test_sessions = [s.strip() for s in args.test.split(',')] if args.test else []
    elif args.auto:
        names = [s[0] for s in sessions]
        n = len(names)
        if n == 1:
            train_sessions = names
        elif n == 2:
            train_sessions = names[:1]
            val_sessions = names[1:]
        else:
            n_train = max(1, int(n * 0.7))
            n_val = max(1, int(n * 0.2))
            train_sessions = names[:n_train]
            val_sessions = names[n_train:n_train + n_val]
            test_sessions = names[n_train + n_val:]
    else:
        # Interactive
        print("Assign each session to a split (t=train, v=val, e=test, s=skip):")
        for name, count in sessions:
            while True:
                choice = input(f"  {name} ({count} frames) [t/v/e/s]: ").strip().lower()
                if choice in ('t', 'v', 'e', 's'):
                    break
            if choice == 't':
                train_sessions.append(name)
            elif choice == 'v':
                val_sessions.append(name)
            elif choice == 'e':
                test_sessions.append(name)
        print()

    # Verify sessions exist
    session_names = {s[0] for s in sessions}
    for split_name, split_list in [("train", train_sessions), ("val", val_sessions), ("test", test_sessions)]:
        for s in split_list:
            if s not in session_names:
                print(f"[WARNING] Session '{s}' not found in {args.indir}/")

    # Build dataset
    print(f"[+] Building dataset in '{args.outdir}/'...")
    counts = {"train": 0, "val": 0, "test": 0}

    for s in train_sessions:
        n = copy_session(s, args.indir, args.outdir, "train", args.labelsdir)
        counts["train"] += n
        print(f"    train ← {s} ({n} frames)")

    for s in val_sessions:
        n = copy_session(s, args.indir, args.outdir, "val", args.labelsdir)
        counts["val"] += n
        print(f"    val   ← {s} ({n} frames)")

    for s in test_sessions:
        n = copy_session(s, args.indir, args.outdir, "test", args.labelsdir)
        counts["test"] += n
        print(f"    test  ← {s} ({n} frames)")

    # Create data.yaml
    yaml_path = create_data_yaml(args.outdir)

    print(f"\n{'=' * 50}")
    print(f"  Dataset ready!")
    print(f"  Train: {counts['train']} | Val: {counts['val']} | Test: {counts['test']}")
    print(f"  data.yaml: {yaml_path}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
