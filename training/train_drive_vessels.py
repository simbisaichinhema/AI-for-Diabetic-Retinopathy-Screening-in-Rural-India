"""DRIVE retinal vessel segmentation training pipeline.

Trains a vessel segmentation model on the DRIVE dataset.
Provides structural evidence for DR screening pipeline.

NOTE: Vessel segmentation itself does NOT diagnose DR.
It provides structural evidence for the main pipeline.
"""

import os
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import EfficientNetB0

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class DRIVEDataset:
    """Load DRIVE vessel segmentation dataset."""

    def __init__(self, data_dir: str = "data/drive"):
        self.data_dir = Path(data_dir)
        self.images = []
        self.masks = []
        self.gold_masks = []

    def load_data(self) -> Dict[str, Any]:
        """Load DRIVE images and vessel masks.

        DRIVE structure:
        - data/drive/training/images/*.tif
        - data/drive/training/1st_manual/*.gif
        - data/drive/test/images/*.tif
        - data/drive/test/1st_manual/*.gif

        Returns:
            Dataset information.
        """
        # Training images
        train_images_dir = self.data_dir / "training" / "images"
        train_masks_dir = self.data_dir / "training" / "1st_manual"

        test_images_dir = self.data_dir / "test" / "images"
        test_masks_dir = self.data_dir / "test" / "1st_manual"

        # Find training images
        if train_images_dir.exists():
            for img_path in sorted(train_images_dir.glob("*.tif")):
                self.images.append({
                    "path": str(img_path),
                    "split": "train",
                })

                # Find corresponding mask
                mask_path = train_masks_dir / f"{img_path.stem}_manual1.gif"
                if mask_path.exists():
                    self.masks.append(str(mask_path))

        # Find test images
        if test_images_dir.exists():
            for img_path in sorted(test_images_dir.glob("*.tif")):
                self.images.append({
                    "path": str(img_path),
                    "split": "test",
                })

                mask_path = test_masks_dir / f"{img_path.stem}_manual1.gif"
                if mask_path.exists():
                    self.masks.append(str(mask_path))

        info = {
            "total_images": len(self.images),
            "train_images": sum(1 for x in self.images if x["split"] == "train"),
            "test_images": sum(1 for x in self.images if x["split"] == "test"),
            "masks_available": len(self.masks),
        }

        return info

    def load_image_and_mask(
        self,
        image_path: str,
        mask_path: str,
        target_size: Tuple[int, int] = (224, 224),
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Load a single image and mask pair."""
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, target_size)
        image = image.astype(np.float32) / 255.0

        # Load vessel mask (GIF format)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, target_size)
        mask = (mask > 127).astype(np.float32)

        return image, mask


def build_vessel_segmentation_model(
    input_shape: Tuple[int, int, int] = (224, 224, 3),
) -> Model:
    """Build U-Net style vessel segmentation model.

    Uses EfficientNetB0 encoder with decoder.

    Args:
        input_shape: Input image shape.

    Returns:
        Keras Model for vessel segmentation.
    """
    inputs = layers.Input(shape=input_shape)

    # Encoder
    encoder = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_tensor=inputs,
    )

    # Skip connections
    skips = [
        encoder.get_layer("block2a_expand_activation").output,
        encoder.get_layer("block3a_expand_activation").output,
        encoder.get_layer("block4a_expand_activation").output,
        encoder.output,
    ]

    # Decoder
    x = encoder.output
    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Concatenate()([x, skips[-1]])
    x = layers.Conv2D(256, 3, padding="same", activation="relu")(x)

    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Concatenate()([x, skips[-2]])
    x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)

    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Concatenate()([x, skips[-3]])
    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)

    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Concatenate()([x, skips[-4]])
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)

    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Conv2D(16, 3, padding="same", activation="relu")(x)

    # Output
    outputs = layers.Conv2D(1, 1, activation="sigmoid")(x)

    model = Model(inputs=inputs, outputs=outputs, name="vessel_segmentation")
    return model


def train_vessel_model(
    data_dir: str = "data/drive",
    output_dir: str = "models/drive",
    config_path: str = "configs/config.yaml",
) -> Tuple[Model, Dict[str, Any]]:
    """Train vessel segmentation model.

    Args:
        data_dir: DRIVE data directory.
        output_dir: Output directory for model.
        config_path: Config file path.

    Returns:
        (trained_model, training_history)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    target_size = tuple(config["image"]["size"])

    # Load data
    dataset = DRIVEDataset(data_dir=data_dir)
    info = dataset.load_data()

    print(f"Loaded {info['total_images']} images")
    print(f"Train: {info['train_images']}, Test: {info['test_images']}")
    print(f"Masks available: {info['masks_available']}")

    if info["masks_available"] == 0:
        print("WARNING: No vessel masks found!")
        print("Please download DRIVE dataset from: https://drive.grand-challenge.org/")

    # Build model
    model = build_vessel_segmentation_model(
        input_shape=(target_size[0], target_size[1], 3),
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    print(f"Model built: {model.count_params():,} parameters")

    # Save model architecture
    model_json = model.to_json()
    with open(output_path / "vessel_model_architecture.json", "w") as f:
        f.write(model_json)

    metadata = {
        "model_name": "vessel_segmentation",
        "input_shape": config["image"]["size"],
        "total_images": info["total_images"],
        "status": "model_built_not_trained",
        "note": "Model architecture created. Train with actual DRIVE dataset.",
    }

    with open(output_path / "vessel_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to {output_path}")
    print("NOTE: Model is NOT TRAINED. Train with actual DRIVE dataset.")

    return model, metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train DRIVE vessel segmentation")
    parser.add_argument("--data-dir", default="data/drive")
    parser.add_argument("--output", default="models/drive")
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()

    model, history = train_vessel_model(
        data_dir=args.data_dir,
        output_dir=args.output,
        config_path=args.config,
    )
