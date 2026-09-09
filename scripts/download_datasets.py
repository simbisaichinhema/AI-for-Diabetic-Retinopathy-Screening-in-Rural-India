#!/usr/bin/env python3
"""Download and prepare datasets for DR screening.

Usage:
    python scripts/download_datasets.py --dataset aptos
    python scripts/download_datasets.py --dataset all

Requires Kaggle API credentials (~/.kaggle/kaggle.json).
Get credentials from: https://www.kaggle.com/settings
"""

import os
import sys
import subprocess
import zipfile
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def check_kaggle_credentials():
    """Check if Kaggle API credentials exist."""
    cred_path = Path.home() / ".kaggle" / "kaggle.json"
    if not cred_path.exists():
        print("ERROR: Kaggle credentials not found!")
        print(f"Expected: {cred_path}")
        print("\nTo set up:")
        print("1. Go to https://www.kaggle.com/settings")
        print("2. Create API token")
        print("3. Place kaggle.json in ~/.kaggle/")
        print("4. Run: chmod 600 ~/.kaggle/kaggle.json")
        return False
    return True


def download_aptos():
    """Download APTOS 2019 Blindness Detection dataset."""
    print("\n=== Downloading APTOS 2019 ===")
    target_dir = DATA_DIR / "aptos"
    target_dir.mkdir(parents=True, exist_ok=True)

    if (target_dir / "train.csv").exists():
        print("APTOS data already exists. Skipping download.")
        return True

    try:
        result = subprocess.run(
            ["kaggle", "competitions", "download", "-c",
             "aptos2019-blindness-detection", "-p", str(target_dir)],
            capture_output=True, text=True, check=True
        )
        print(result.stdout)

        # Extract zip files
        for zip_file in target_dir.glob("*.zip"):
            print(f"Extracting {zip_file.name}...")
            with zipfile.ZipFile(zip_file, 'r') as z:
                z.extractall(target_dir)
            zip_file.unlink()

        return True
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("kaggle CLI not found. Install with: pip install kaggle")
        return False


def download_idrid():
    """Download IDRiD dataset."""
    print("\n=== Downloading IDRiD ===")
    print("IDRiD requires manual download from: https://idrid.grand-challenge.org/")
    print("After downloading, extract to: data/idrid/")
    print("\nIDRiD provides:")
    print("- 516 training images")
    print("- DR grade labels")
    print("- Lesion segmentation masks")
    return False


def download_drive():
    """Download DRIVE dataset."""
    print("\n=== Downloading DRIVE ===")
    print("DRIVE requires manual download from: https://drive.grand-challenge.org/")
    print("After downloading, extract to: data/drive/")
    print("\nDRIVE provides:")
    print("- 40 retinal images")
    print("- Vessel segmentation masks")
    return False


def download_messidor2():
    """Download Messidor-2 dataset."""
    print("\n=== Downloading Messidor-2 ===")
    print("Messidor-2 requires registration at: http://www.adris.net/messidor2")
    print("After downloading, extract to: data/messidor2/")
    print("\nMessidor-2 provides:")
    print("- 1748 retinal images")
    print("- DR grades and risk of macular edema")
    return False


def create_sample_aptos():
    """Create a small sample APTOS-like dataset for testing."""
    print("\n=== Creating sample APTOS dataset for testing ===")
    target_dir = DATA_DIR / "aptos"
    target_dir.mkdir(parents=True, exist_ok=True)

    images_dir = target_dir / "train_images"
    images_dir.mkdir(exist_ok=True)

    import numpy as np
    from PIL import Image, ImageDraw

    # Create sample images with different patterns per class
    np.random.seed(42)
    samples_per_class = 20

    rows = []
    for cls in range(5):
        for i in range(samples_per_class):
            img_id = f"sample_{cls:02d}_{i:03d}"

            # Create synthetic fundus-like image
            img = np.random.randint(20, 200, (224, 224, 3), dtype=np.uint8)

            # Add some structure based on class
            center = (112, 112)
            radius = 80 - cls * 5
            y, x = np.ogrid[-112:112, -112:112]
            mask = x*x + y*y <= radius*radius

            img[mask] = img[mask] // 2 + np.array([100, 60, 30], dtype=np.uint8)

            # Add class-specific patterns (lesion-like dots)
            pil_img = Image.fromarray(img)
            draw = ImageDraw.Draw(pil_img)
            if cls >= 1:
                for _ in range(cls * 3):
                    cx, cy = np.random.randint(40, 184, 2)
                    r = np.random.randint(1, 3)
                    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(180, 20, 20))

            pil_img.save(images_dir / f"{img_id}.png")
            rows.append(f"{img_id},{cls}")

    # Write CSV
    with open(target_dir / "train.csv", "w") as f:
        f.write("id_code,diagnosis\n")
        f.write("\n".join(rows))
        f.write("\n")

    print(f"Created {5 * samples_per_class} sample images in {images_dir}")
    print(f"Created train.csv with class distribution")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download DR screening datasets")
    parser.add_argument("--dataset", choices=["aptos", "idrid", "drive", "messidor2", "all", "sample"],
                       default="sample", help="Dataset to download")
    args = parser.parse_args()

    if args.dataset == "sample":
        create_sample_aptos()
    elif args.dataset == "aptos":
        if check_kaggle_credentials():
            download_aptos()
    elif args.dataset == "idrid":
        download_idrid()
    elif args.dataset == "drive":
        download_drive()
    elif args.dataset == "messidor2":
        download_messidor2()
    elif args.dataset == "all":
        if check_kaggle_credentials():
            download_aptos()
        download_idrid()
        download_drive()
        download_messidor2()
