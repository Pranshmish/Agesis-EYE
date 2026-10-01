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


def copy_file_pair(img_src, label_name, src_dir, outdir, split, labelsdir, session_name):
    img_dst = os.path.join(outdir, "images", split)
    lbl_dst = os.path.join(outdir, "labels", split)
    os.makedirs(img_dst, exist_ok=True)
    os.makedirs(lbl_dst, exist_ok=True)

    f = os.path.basename(img_src)
    shutil.copy2(img_src, os.path.join(img_dst, f))

    label_found = False
    for lbl_src in [
        os.path.join(src_dir, label_name),
        os.path.join(labelsdir, session_name, label_name),
        os.path.join(labelsdir, label_name),
    ]:
        if os.path.exists(lbl_src):
            shutil.copy2(lbl_src, os.path.join(lbl_dst, label_name))
            label_found = True
            break

    meta_path = os.path.join(src_dir, f.replace('.jpg', '.json'))
    if not label_found and os.path.exists(meta_path):
        import json
        try:
            with open(meta_path) as mf:
                meta = json.load(mf)
                if meta.get("negative", False):
                    open(os.path.join(lbl_dst, label_name), 'w').close()
                    label_found = True
        except Exception:
            pass

    if not label_found:
        open(os.path.join(lbl_dst, label_name), 'w').close()


def copy_session(session_name, indir, outdir, split, labelsdir):
    """Copy an entire session's images and labels into the dataset split."""
    src_dir = os.path.join(indir, session_name)
    copied = 0
    for f in sorted(os.listdir(src_dir)):
        if not f.endswith('.jpg') or "preview" in f or "result" in f:
            continue
        copy_file_pair(os.path.join(src_dir, f), f.replace('.jpg', '.txt'),
                       src_dir, outdir, split, labelsdir, session_name)
        copied += 1
    return copied


def copy_session_partitioned(session_name, indir, outdir, labelsdir, train_ratio=0.7, val_ratio=0.2):
    """Partition a single session's frames into train, val, test chunks."""
    src_dir = os.path.join(indir, session_name)
    all_files = [f for f in sorted(os.listdir(src_dir))
                 if f.endswith('.jpg') and "preview" not in f and "result" not in f]
    n = len(all_files)
    n_train = max(1, int(n * train_ratio))
    n_val = max(1, int(n * val_ratio))

    train_files = all_files[:n_train]
    val_files = all_files[n_train:n_train + n_val]
    test_files = all_files[n_train + n_val:]

    counts = {"train": 0, "val": 0, "test": 0}
    for f in train_files:
        copy_file_pair(os.path.join(src_dir, f), f.replace('.jpg', '.txt'),
                       src_dir, outdir, "train", labelsdir, session_name)
        counts["train"] += 1

    for f in val_files:
        copy_file_pair(os.path.join(src_dir, f), f.replace('.jpg', '.txt'),
                       src_dir, outdir, "val", labelsdir, session_name)
        counts["val"] += 1

    for f in test_files:
        copy_file_pair(os.path.join(src_dir, f), f.replace('.jpg', '.txt'),
                       src_dir, outdir, "test", labelsdir, session_name)
        counts["test"] += 1

    return counts


def create_data_yaml(outdir, class_names=None):
    """Create YOLO data.yaml file with relative path for Kaggle/local portability."""
    if class_names is None:
        class_names = {0: "balloon"}

    data = {
        "path": ".",
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
            f.write("path: .\n")
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
        print(f"    {name:30s} -> {count} frames")
        total_frames += count
    print(f"    {'TOTAL':30s} -> {total_frames} frames\n")

    # Determine splits
    train_sessions = []
    val_sessions = []
    test_sessions = []

    if args.train:
        train_sessions = [s.strip() for s in args.train.split(',')]
        val_sessions = [s.strip() for s in args.val.split(',')] if args.val else []
        test_sessions = [s.strip() for s in args.test.split(',')] if args.test else []
    elif args.auto:
        # Auto mode: if 1 or 2 sessions, partition by frames to guarantee train, val, and test splits
        print(f"[+] Auto-partitioning frames into 70% train, 20% val, 10% test...")
        for sub in ["images", "labels"]:
            subpath = os.path.join(args.outdir, sub)
            if os.path.exists(subpath):
                shutil.rmtree(subpath)
        total_counts = {"train": 0, "val": 0, "test": 0}
        for name, _ in sessions:
            c = copy_session_partitioned(name, args.indir, args.outdir, args.labelsdir)
            total_counts["train"] += c["train"]
            total_counts["val"] += c["val"]
            total_counts["test"] += c["test"]
            print(f"    {name}: train={c['train']}, val={c['val']}, test={c['test']}")

        yaml_path = create_data_yaml(args.outdir)
        print(f"\n{'=' * 50}")
        print(f"  Dataset ready!")
        print(f"  Train: {total_counts['train']} | Val: {total_counts['val']} | Test: {total_counts['test']}")
        print(f"  data.yaml: {yaml_path}")
        print(f"{'=' * 50}")
        return
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
        print(f"    train <- {s} ({n} frames)")

    for s in val_sessions:
        n = copy_session(s, args.indir, args.outdir, "val", args.labelsdir)
        counts["val"] += n
        print(f"    val   <- {s} ({n} frames)")

    for s in test_sessions:
        n = copy_session(s, args.indir, args.outdir, "test", args.labelsdir)
        counts["test"] += n
        print(f"    test  <- {s} ({n} frames)")

    # Create data.yaml
    yaml_path = create_data_yaml(args.outdir)

    print(f"\n{'=' * 50}")
    print(f"  Dataset ready!")
    print(f"  Train: {counts['train']} | Val: {counts['val']} | Test: {counts['test']}")
    print(f"  data.yaml: {yaml_path}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
