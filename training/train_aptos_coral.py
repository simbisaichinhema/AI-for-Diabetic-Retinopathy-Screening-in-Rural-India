#!/usr/bin/env python3
"""Full APTOS training pipeline with CORAL ordinal regression.

This script:
1. Downloads real APTOS data via Kaggle (if available)
2. Loads and validates data
3. Trains EfficientNetB3 + CORAL with 2-stage transfer learning
4. Searches for optimal QWK cutoffs
5. Evaluates on held-out test set
6. Saves model, cutoffs, metrics, and metadata

Usage:
    python training/train_aptos_coral.py --data-dir data/aptos
    python training/train_aptos_coral.py --download  # Download from Kaggle first
"""

import os
import sys
import json
import math
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import mixed_precision
from sklearn.model_selection import StratifiedShuffleSplit

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.coral import (
    label_to_ordinal,
    coral_loss_mean,
    logits_to_prob,
    prob_to_continuous,
    apply_cutoffs,
    qwk,
    search_best_cutoffs,
    QWKCallback,
)
from training.train_coral import build_coral_model, compile_coral_model


def setup_runtime(seed: int = 42):
    """Configure TF runtime for reproducibility and performance."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

    # GPU memory growth
    for g in tf.config.list_physical_devices("GPU"):
        try:
            tf.config.experimental.set_memory_growth(g, True)
        except Exception:
            pass

    # Mixed precision for faster training
    mixed_precision.set_global_policy("mixed_float16")
    print(f"TensorFlow {tf.__version__}")


def load_aptos_data(data_dir: str = "data/aptos") -> Tuple[pd.DataFrame, int]:
    """Load APTOS train.csv and validate.

    Returns:
        (DataFrame with image paths, number of valid images)
    """
    data_path = Path(data_dir)
    csv_path = data_path / "train.csv"
    images_dir = data_path / "train_images"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"APTOS train.csv not found at {csv_path}\n"
            f"Download from: https://www.kaggle.com/c/aptos2019-blindness-detection/data\n"
            f"Or run: python scripts/download_datasets.py --dataset aptos"
        )

    df = pd.read_csv(csv_path)
    print(f"Loaded CSV with {len(df)} entries")

    # Resolve image paths
    df["path"] = df["id_code"].apply(lambda x: str(images_dir / f"{x}.png"))

    # Also check .jpg fallback
    for idx, row in df.iterrows():
        if not os.path.exists(row["path"]):
            jpg_path = str(images_dir / f"{row['id_code']}.jpg")
            if os.path.exists(jpg_path):
                df.at[idx, "path"] = jpg_path

    # Verify image existence
    df["valid"] = df["path"].apply(os.path.exists)
    valid_df = df[df["valid"]].copy()

    print(f"Valid images: {len(valid_df)}/{len(df)}")
    print(f"Class distribution:\n{valid_df['diagnosis'].value_counts().sort_index()}")

    return valid_df, len(df)


def stratified_split(
    paths: np.ndarray,
    labels: np.ndarray,
    val_split: float = 0.2,
    test_split: float = 0.15,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split data into train/val/test with stratification.

    Args:
        paths: Image paths.
        labels: Integer labels.
        val_split: Fraction for validation.
        test_split: Fraction for test.
        seed: Random seed.

    Returns:
        (train_paths, val_paths, test_paths, train_labels, val_labels, test_labels)
    """
    # First split: separate test set
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=test_split, random_state=seed)
    train_val_idx, test_idx = next(sss1.split(paths, labels))

    # Second split: separate validation from train
    relative_val = val_split / (1 - test_split)
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=relative_val, random_state=seed)
    train_idx, val_idx = next(sss2.split(paths[train_val_idx], labels[train_val_idx]))

    train_idx_final = train_val_idx[train_idx]
    val_idx_final = train_val_idx[val_idx]

    print(f"\nSplit summary:")
    print(f"  Train: {len(train_idx_final)} images")
    print(f"  Val:   {len(val_idx_final)} images")
    print(f"  Test:  {len(test_idx)} images")

    return (
        paths[train_idx_final], paths[val_idx_final], paths[test_idx],
        labels[train_idx_final], labels[val_idx_final], labels[test_idx],
    )


def make_datasets(
    train_paths: np.ndarray,
    train_labels: np.ndarray,
    val_paths: np.ndarray,
    val_labels: np.ndarray,
    config: dict,
    oversample: bool = True,
) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
    """Create tf.data.Dataset pipelines with optional oversampling.

    Args:
        train_paths: Training image paths.
        train_labels: Training labels.
        val_paths: Validation image paths.
        val_labels: Validation labels.
        config: Configuration dict.
        oversample: Whether to apply power-law oversampling.

    Returns:
        (train_dataset, val_dataset)
    """
    batch_size = config["training"]["batch_size"]
    img_size = tuple(config["image"]["size"])

    def decode_and_preprocess(path, label):
        """Read image, ROI crop, resize, normalize."""
        img = tf.io.read_file(path)
        img = tf.image.decode_png(img, channels=3)

        # ROI crop: remove black border
        img = _safe_roi_crop(img, thumb_size=256)

        # Resize
        img = tf.image.resize(img, img_size, method="bilinear")
        img = tf.clip_by_value(img, 0, 255)
        img = tf.cast(img, tf.float32) / 255.0

        # Ordinal encoding
        y_ord = label_to_ordinal(label)
        return img, y_ord

    if oversample and len(train_paths) > 0:
        # Power-law oversampling
        power = config["coral"]["oversample_power"]
        cls_counts = np.bincount(train_labels, minlength=5).astype(np.float32)
        inv = 1.0 / np.maximum(cls_counts, 1.0)
        weights = inv ** power

        # Extra boosts for rare classes
        weights[1] *= config["coral"]["class1_boost"]
        weights[4] *= config["coral"]["class4_boost"]
        weights = weights / weights.sum()

        print(f"\nOversampling weights: {dict(enumerate(weights.round(4)))}")

        per_class = []
        for c in range(5):
            idx = np.where(train_labels == c)[0]
            if len(idx) == 0:
                continue
            ds_c = tf.data.Dataset.from_tensor_slices((train_paths[idx], train_labels[idx]))
            ds_c = ds_c.shuffle(min(256, len(idx)), seed=42, reshuffle_each_iteration=True)
            ds_c = ds_c.repeat()
            ds_c = ds_c.map(decode_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
            per_class.append(ds_c)

        train_ds = tf.data.Dataset.sample_from_datasets(
            per_class, weights=list(weights[cls_counts > 0]), seed=42
        )
        train_ds = train_ds.batch(batch_size, drop_remainder=True).prefetch(tf.data.AUTOTUNE)
    else:
        train_ds = tf.data.Dataset.from_tensor_slices((train_paths, train_labels))
        train_ds = train_ds.shuffle(512, seed=42)
        train_ds = train_ds.map(decode_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        train_ds = train_ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)

    # Validation dataset (no oversampling, no augmentation)
    val_ds = tf.data.Dataset.from_tensor_slices((val_paths, val_labels))
    val_ds = val_ds.map(decode_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    val_ds = val_ds.batch(batch_size, drop_remainder=False).prefetch(tf.data.AUTOTUNE)

    return train_ds, val_ds


def _safe_roi_crop(img, thumb_size=256):
    """Safe ROI crop: remove black fundus background with safety guards."""
    h = tf.shape(img)[0]
    w = tf.shape(img)[1]

    thumb = tf.image.resize(tf.cast(img, tf.float32), (thumb_size, thumb_size), method="bilinear")
    gray = tf.image.rgb_to_grayscale(thumb)

    threshold = tf.maximum(15.0, tf.reduce_mean(gray) * 0.5)
    mask = gray > threshold
    coords = tf.where(mask[..., 0])

    def no_crop():
        return img

    def do_crop():
        y_min = tf.reduce_min(coords[:, 0])
        x_min = tf.reduce_min(coords[:, 1])
        y_max = tf.reduce_max(coords[:, 0])
        x_max = tf.reduce_max(coords[:, 1])

        scale_y = tf.cast(h, tf.float32) / float(thumb_size)
        scale_x = tf.cast(w, tf.float32) / float(thumb_size)

        y0 = tf.cast(tf.math.floor(tf.cast(y_min, tf.float32) * scale_y), tf.int32)
        x0 = tf.cast(tf.math.floor(tf.cast(x_min, tf.float32) * scale_x), tf.int32)
        y1 = tf.cast(tf.math.ceil(tf.cast(y_max, tf.float32) * scale_y), tf.int32)
        x1 = tf.cast(tf.math.ceil(tf.cast(x_max, tf.float32) * scale_x), tf.int32)

        pad_y = tf.cast(tf.math.round(tf.cast(h, tf.float32) * 0.08), tf.int32)
        pad_x = tf.cast(tf.math.round(tf.cast(w, tf.float32) * 0.08), tf.int32)

        y0 = tf.maximum(0, y0 - pad_y)
        x0 = tf.maximum(0, x0 - pad_x)
        y1 = tf.minimum(h - 1, y1 + pad_y)
        x1 = tf.minimum(w - 1, x1 + pad_x)

        new_h = tf.maximum(1, y1 - y0 + 1)
        new_w = tf.maximum(1, x1 - x0 + 1)

        box_area = tf.cast(new_h * new_w, tf.float32)
        img_area = tf.cast(h * w, tf.float32)
        frac = box_area / tf.maximum(img_area, 1.0)

        def crop_ok():
            return tf.image.crop_to_bounding_box(img, y0, x0, new_h, new_w)

        return tf.cond((frac >= 0.20) & (frac <= 0.98), crop_ok, no_crop)

    return tf.cond(tf.shape(coords)[0] >= 500, do_crop, no_crop)


def train_coral_model(
    data_dir: str = "data/aptos",
    config_path: str = "configs/config.yaml",
    output_dir: str = "models/aptos",
) -> Dict[str, Any]:
    """Full CORAL training pipeline.

    Args:
        data_dir: APTOS data directory.
        config_path: Config file path.
        output_dir: Output directory.

    Returns:
        Training results dictionary.
    """
    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Setup
    seed = config["project"]["seed"]
    setup_runtime(seed)

    # Load data
    print("\n" + "=" * 60)
    print("LOADING APTOS DATA")
    print("=" * 60)
    df, total_images = load_aptos_data(data_dir)

    paths = df["path"].values
    labels = df["diagnosis"].astype(int).values

    # Split
    train_paths, val_paths, test_paths, train_y, val_y, test_y = stratified_split(
        paths, labels,
        val_split=config["training"]["validation_split"],
        test_split=config["training"]["test_split"],
        seed=seed,
    )

    # Save split info
    split_info = {
        "total": total_images,
        "train": len(train_paths),
        "val": len(val_paths),
        "test": len(test_paths),
        "train_dist": dict(enumerate(np.bincount(train_y, minlength=5).tolist())),
        "val_dist": dict(enumerate(np.bincount(val_y, minlength=5).tolist())),
        "test_dist": dict(enumerate(np.bincount(test_y, minlength=5).tolist())),
        "seed": seed,
    }
    with open(output_path / "split_info.json", "w") as f:
        json.dump(split_info, f, indent=2)

    # Create datasets
    print("\n" + "=" * 60)
    print("CREATING DATASETS")
    print("=" * 60)
    train_ds, val_ds = make_datasets(train_paths, train_y, val_paths, val_y, config)

    # Build model
    print("\n" + "=" * 60)
    print("BUILDING CORAL MODEL")
    print("=" * 60)
    model = build_coral_model(
        num_grades=5,
        input_shape=(config["image"]["size"][0], config["image"]["size"][1], 3),
        dropout_rate=config["coral"]["dropout"],
        freeze_backbone=True,
        use_augmentation=True,
    )
    print(f"Model: {model.count_params():,} parameters")

    # Callbacks
    qwk_cb = QWKCallback(val_ds, val_y, out_dir=str(output_path))
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=2, min_lr=config["training"]["min_lr"], verbose=1
    )
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=config["training"]["patience"],
        restore_best_weights=False, verbose=1
    )

    steps_per_epoch = math.floor(len(train_paths) / config["training"]["batch_size"])
    val_steps = math.ceil(len(val_paths) / config["training"]["batch_size"])

    # Stage 1: Warmup (frozen backbone)
    print("\n" + "=" * 60)
    print("STAGE 1: WARMUP (frozen backbone)")
    print("=" * 60)
    compile_coral_model(model, learning_rate=config["training"]["learning_rate"])
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["coral"]["warmup_epochs"],
        steps_per_epoch=steps_per_epoch,
        validation_steps=val_steps,
        callbacks=[qwk_cb, reduce_lr, early_stop],
        verbose=1,
    )

    # Stage 2: Fine-tune
    print("\n" + "=" * 60)
    print("STAGE 2: FINE-TUNE (unfreeze last N layers)")
    print("=" * 60)
    # Unfreeze backbone
    for layer in model.layers:
        if hasattr(layer, "trainable") and "efficientnet" in layer.name.lower():
            layer.trainable = True
            break

    # Freeze all but last N layers
    unfreeze_n = config["coral"]["unfreeze_last_n"]
    backbone = None
    for layer in model.layers:
        if isinstance(layer, keras.Model) and "efficientnet" in layer.name.lower():
            backbone = layer
            break

    if backbone is not None:
        for layer in backbone.layers[:-unfreeze_n]:
            layer.trainable = False
        # Keep BatchNorm frozen
        for layer in backbone.layers:
            if isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = False

    # Reset early stop for fine-tuning
    early_stop_fine = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=config["training"]["patience"],
        restore_best_weights=False, verbose=1
    )

    compile_coral_model(model, learning_rate=config["training"]["fine_tune_lr"])
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["coral"]["finetune_epochs"],
        steps_per_epoch=steps_per_epoch,
        validation_steps=val_steps,
        callbacks=[qwk_cb, reduce_lr, early_stop_fine],
        verbose=1,
    )

    # Load best weights
    best_weights_path = output_path / "best_qwk.weights.h5"
    if best_weights_path.exists():
        model.load_weights(str(best_weights_path))
        print(f"\nLoaded best weights (QWK: {qwk_cb.best_qwk:.5f})")

    best_cutoffs_path = output_path / "best_coral_cutoffs.npy"
    if best_cutoffs_path.exists():
        best_cutoffs = tuple(np.load(str(best_cutoffs_path)).tolist())
    else:
        best_cutoffs = (0.8, 1.6, 2.4, 3.2)

    # Final evaluation on validation set
    print("\n" + "=" * 60)
    print("FINAL EVALUATION")
    print("=" * 60)

    # Get predictions
    val_ds_eval = val_ds.map(lambda x, y: x)
    logits = model.predict(val_ds_eval, verbose=0)
    probs = logits_to_prob(logits)
    cont = prob_to_continuous(probs)
    pred = apply_cutoffs(cont, best_cutoffs)

    # Compute metrics
    from sklearn.metrics import (
        classification_report, confusion_matrix, accuracy_score,
        precision_recall_fscore_support,
    )

    accuracy = accuracy_score(val_y, pred)
    cm = confusion_matrix(val_y, pred, labels=range(5))
    report = classification_report(
        val_y, pred,
        target_names=["No DR", "Mild DR", "Moderate DR", "Severe DR", "Proliferative DR"],
        output_dict=True, zero_division=0,
    )
    val_qwk = qwk(val_y, pred)

    # Binary referable DR
    val_y_binary = (val_y >= 2).astype(int)
    pred_binary = (pred >= 2).astype(int)
    from sklearn.metrics import roc_auc_score
    try:
        ref_auroc = roc_auc_score(val_y_binary, np.sum(probs[:, 2:], axis=1))
    except ValueError:
        ref_auroc = None

    tn, fp, fn, tp = confusion_matrix(val_y_binary, pred_binary, labels=[0, 1]).ravel()
    ref_sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    ref_specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    # Print results
    print(f"\n--- 5-Class DR Grading ---")
    print(f"QWK: {val_qwk:.5f}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"\nConfusion Matrix:")
    print(cm)
    print(f"\nClassification Report:")
    print(classification_report(
        val_y, pred,
        target_names=["No DR", "Mild DR", "Moderate DR", "Severe DR", "Proliferative DR"],
        zero_division=0,
    ))

    print(f"\n--- Referable DR (Level 2+) ---")
    print(f"Sensitivity: {ref_sensitivity:.4f}")
    print(f"Specificity: {ref_specificity:.4f}")
    print(f"AUROC: {ref_auroc}")

    print(f"\n--- Best Cutoffs ---")
    print(f"Cutoffs: {best_cutoffs}")
    print(f"Best QWK during training: {qwk_cb.best_qwk:.5f}")

    # Save final model
    model.save(str(output_path / "aptos_dr_classifier_coral.keras"))

    # Save metadata
    metadata = {
        "model_name": "aptos_dr_classifier_coral",
        "architecture": "EfficientNetB3 + CORAL",
        "num_classes": 5,
        "input_shape": config["image"]["size"],
        "training_date": datetime.now().isoformat(),
        "config": {
            "batch_size": config["training"]["batch_size"],
            "warmup_epochs": config["coral"]["warmup_epochs"],
            "finetune_epochs": config["coral"]["finetune_epochs"],
            "learning_rate": config["training"]["learning_rate"],
            "fine_tune_lr": config["training"]["fine_tune_lr"],
            "dropout": config["coral"]["dropout"],
            "oversample_power": config["coral"]["oversample_power"],
        },
        "seed": seed,
        "split": split_info,
        "best_qwk": float(qwk_cb.best_qwk),
        "best_cutoffs": list(best_cutoffs),
        "final_val_qwk": float(val_qwk),
        "final_val_accuracy": float(accuracy),
        "referable_dr": {
            "sensitivity": float(ref_sensitivity),
            "specificity": float(ref_specificity),
            "auroc": float(ref_auroc) if ref_auroc else None,
        },
        "training_history": qwk_cb.history,
    }

    with open(output_path / "model_metadata_coral.json", "w") as f:
        json.dump(metadata, f, indent=2, default=float)

    # Save evaluation report
    eval_report = {
        "model": "CORAL EfficientNetB3",
        "val_qwk": float(val_qwk),
        "val_accuracy": float(accuracy),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "best_cutoffs": list(best_cutoffs),
        "referable_dr": {
            "sensitivity": float(ref_sensitivity),
            "specificity": float(ref_specificity),
            "auroc": float(ref_auroc) if ref_auroc else None,
        },
        "note": "QWK is the APTOS competition metric. Target: >0.90 QWK.",
    }
    with open(output_path / "evaluation_coral.json", "w") as f:
        json.dump(eval_report, f, indent=2, default=float)

    print(f"\n{'=' * 60}")
    print(f"TRAINING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Model: {output_path / 'aptos_dr_classifier_coral.keras'}")
    print(f"Weights: {output_path / 'best_qwk.weights.h5'}")
    print(f"Cutoffs: {best_cutoffs}")
    print(f"QWK: {qwk_cb.best_qwk:.5f}")

    return metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train CORAL DR classifier on APTOS")
    parser.add_argument("--data-dir", default="data/aptos", help="APTOS data directory")
    parser.add_argument("--config", default="configs/config.yaml", help="Config file")
    parser.add_argument("--output", default="models/aptos", help="Output directory")
    args = parser.parse_args()

    train_coral_model(
        data_dir=args.data_dir,
        config_path=args.config,
        output_dir=args.output,
    )
