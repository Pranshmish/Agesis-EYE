"""
Kaggle API Automation Tool — Upload dataset, push training notebook, and fetch trained weights.

Requirements:
    pip install kaggle

Usage:
    # 1. Setup API key (if not already in ~/.kaggle/kaggle.json)
    python train_kaggle_api.py --setup --username YOUR_USERNAME --key YOUR_KEY

    # 2. Upload dataset to Kaggle
    python train_kaggle_api.py --upload-dataset

    # 3. Push and run the training notebook on Kaggle GPU
    python train_kaggle_api.py --train

    # 4. Check status & download trained models (best.pt, best.onnx)
    python train_kaggle_api.py --download-output
"""
import os
import sys
import json
import shutil
import argparse
import subprocess
import time

DATASET_SLUG = "agesis-balloon-dataset"
KERNEL_SLUG = "agesis-balloon-yolov8-training"


def parse_args():
    p = argparse.ArgumentParser(description="Agesis EYE Kaggle Training Automation")
    p.add_argument("--setup", action="store_true", help="Configure Kaggle credentials")
    p.add_argument("--username", type=str, default="", help="Kaggle username")
    p.add_argument("--key", type=str, default="", help="Kaggle API key (token)")
    p.add_argument("--upload-dataset", action="store_true", help="Upload dataset zip to Kaggle")
    p.add_argument("--train", action="store_true", help="Push and run notebook on Kaggle GPU")
    p.add_argument("--status", action="store_true", help="Check status of running training job")
    p.add_argument("--download-output", action="store_true", help="Download trained model weights")
    p.add_argument("--dataset-zip", default="agesis_balloon_dataset_kaggle.zip", help="Path to dataset zip file")
    return p.parse_args()


def get_kaggle_dir():
    home = os.path.expanduser("~")
    kdir = os.path.join(home, ".kaggle")
    os.makedirs(kdir, exist_ok=True)
    return kdir


def setup_credentials(username, key):
    if not username or not key:
        print("[!] Please provide both --username and --key")
        print("    Find your key at: https://www.kaggle.com/settings -> Create New Token")
        return False
    kdir = get_kaggle_dir()
    cfg_path = os.path.join(kdir, "kaggle.json")
    with open(cfg_path, 'w') as f:
        json.dump({"username": username, "key": key}, f)
    # Set permissions on Linux/Mac if applicable
    try:
        os.chmod(cfg_path, 0o600)
    except Exception:
        pass
    print(f"[+] Credentials saved to: {cfg_path}")
    return True


def check_kaggle_cli():
    try:
        import kaggle
        return True
    except ImportError:
        print("[!] Installing 'kaggle' Python package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle", "-q"])
        return True


def get_username():
    cfg_path = os.path.join(get_kaggle_dir(), "kaggle.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                d = json.load(f)
                return d.get("username", "")
        except Exception:
            pass
    return os.environ.get("KAGGLE_USERNAME", "")


def upload_dataset(zip_path):
    check_kaggle_cli()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    username = get_username()
    if not username:
        print("[ERROR] Kaggle credentials not found. Run with --setup first.")
        sys.exit(1)

    if not os.path.exists(zip_path):
        # Look in workspace root
        alt = os.path.join(os.path.dirname(__file__), "..", zip_path)
        if os.path.exists(alt):
            zip_path = alt
        else:
            print(f"[ERROR] Cannot find dataset zip: {zip_path}")
            sys.exit(1)

    # Prepare staging directory
    staging_dir = os.path.abspath("kaggle_dataset_staging")
    os.makedirs(staging_dir, exist_ok=True)

    # Copy zip or dataset files
    dest_zip = os.path.join(staging_dir, os.path.basename(zip_path))
    shutil.copy2(zip_path, dest_zip)

    # Create dataset-metadata.json
    metadata = {
        "title": "Agesis EYE Black Balloon Dataset",
        "id": f"{username}/{DATASET_SLUG}",
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(os.path.join(staging_dir, "dataset-metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[+] Staging dataset in: {staging_dir}")
    print(f"[+] Uploading dataset '{username}/{DATASET_SLUG}' to Kaggle...")

    try:
        api.dataset_create_new(staging_dir, public=False, quiet=False)
        print("[+] Dataset created successfully on Kaggle!")
    except Exception as e:
        print(f"[!] Dataset creation returned: {e}")
        print("[+] Attempting to create new dataset version instead...")
        try:
            api.dataset_create_version(staging_dir, version_notes="Updated balloon dataset", quiet=False)
            print("[+] Dataset version updated successfully!")
        except Exception as e2:
            print(f"[ERROR] Failed to upload: {e2}")
            return False

    return True


def run_training_kernel():
    check_kaggle_cli()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    username = get_username()
    staging_dir = os.path.abspath("kaggle_kernel_staging")
    os.makedirs(staging_dir, exist_ok=True)

    # Copy notebook
    nb_src = os.path.join(os.path.dirname(__file__), "train_balloon_detector.ipynb")
    nb_dst = os.path.join(staging_dir, "train_balloon_detector.ipynb")
    shutil.copy2(nb_src, nb_dst)

    # kernel-metadata.json
    kernel_metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": "Agesis Balloon YOLOv8 Training",
        "code_file": "train_balloon_detector.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_internet": "true",
        "dataset_sources": [f"{username}/{DATASET_SLUG}"]
    }
    with open(os.path.join(staging_dir, "kernel-metadata.json"), 'w') as f:
        json.dump(kernel_metadata, f, indent=2)

    print(f"[+] Pushing training kernel '{username}/{KERNEL_SLUG}' with GPU enabled...")
    api.kernels_push(staging_dir)
    print(f"[+] Kernel submitted! Running in background on Kaggle GPU.")
    print(f"    Check status with: python train_kaggle_api.py --status")


def check_status():
    check_kaggle_cli()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    username = get_username()
    kernel_ref = f"{username}/{KERNEL_SLUG}"
    status = api.kernels_status(kernel_ref)
    print(f"\n[+] Kernel: {kernel_ref}")
    print(f"[+] Status: {status.get('status', 'unknown')}")
    if status.get("failureMessage"):
        print(f"[!] Error: {status['failureMessage']}")
    return status.get("status")


def download_output():
    check_kaggle_cli()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    username = get_username()
    kernel_ref = f"{username}/{KERNEL_SLUG}"
    out_dir = os.path.abspath("trained_weights")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[+] Downloading output files from '{kernel_ref}' into: {out_dir}")
    api.kernels_output(kernel_ref, path=out_dir)
    print("[+] Download complete! Files saved:")
    for f in os.listdir(out_dir):
        print(f"    - {f}")


def main():
    args = parse_args()

    if args.setup:
        setup_credentials(args.username, args.key)
    elif args.upload_dataset:
        upload_dataset(args.dataset_zip)
    elif args.train:
        run_training_kernel()
    elif args.status:
        check_status()
    elif args.download_output:
        download_output()
    else:
        print("""
Agesis EYE — Kaggle Automation Workflow:
----------------------------------------
1. Setup credentials:
   python train_kaggle_api.py --setup --username <USER> --key <API_KEY>

2. Upload dataset zip:
   python train_kaggle_api.py --upload-dataset

3. Submit training notebook to Kaggle GPU:
   python train_kaggle_api.py --train

4. Check training progress:
   python train_kaggle_api.py --status

5. Download trained best.pt & best.onnx:
   python train_kaggle_api.py --download-output
""")


if __name__ == "__main__":
    main()
