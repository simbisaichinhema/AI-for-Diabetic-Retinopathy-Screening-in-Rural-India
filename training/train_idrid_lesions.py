"""IDRiD lesion detection/segmentation training pipeline.

Uses IDRiD dataset annotations for:
- Microaneurysm segmentation
- Hemorrhage segmentation
- Hard exudate segmentation
- Soft exudate segmentation
- Optic disc segmentation

NOTE: Do NOT invent labels. Only train on available annotations.
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


class IDRiDLesionDataset:
    """Load IDRiD lesion segmentation data."""

    # Available lesion types in IDRiD
    LESION_TYPES = [
        "microaneurysms",
        "hemorrhages",
        "hard_exudates",
        "soft_exudates",
        "optic_disc",
    ]

    def __init__(
        self,
        data_dir: str = "data/idrid",
        lesion_types: Optional[List[str]] = None,
    ):
        self.data_dir = Path(data_dir)
        self.lesion_types = lesion_types or self.LESION_TYPES
        self.images = []
        self.masks = {}

    def load_data(self) -> Dict[str, Any]:
        """Load IDRiD images and masks.

        Returns:
            Dictionary with dataset information.
        """
        # IDRiD directory structure:
        # data/idrid/ODIR-5K/Training/IDRiD_*_*.jpg
        # data/idrid/ODIR-5K/Training/IDRiD_*_*.tif (masks)

        images_dir = self.data_dir / "ODIR-5K" / "Training"
        if not images_dir.exists():
            # Try alternate structure
            images_dir = self.data_dir / "training"

        if not images_dir.exists():
            raise FileNotFoundError(
                f"IDRiD data not found at {self.data_dir}. "
                f"Download from: https://idrid.grand-challenge.org/"
            )

        # Find images
        image_files = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")))

        # Find corresponding masks
        for img_path in image_files:
            img_id = img_path.stem
            self.images.append(str(img_path))

            for lesion in self.lesion_types:
                mask_path = images_dir / f"{img_id}_{lesion}.tif"
                if mask_path.exists():
                    if lesion not in self.masks:
                        self.masks[lesion] = []
                    self.masks[lesion].append(str(mask_path))

        info = {
            "total_images": len(self.images),
            "available_lesions": list(self.masks.keys()),
            "lesion_counts": {k: len(v) for k, v in self.masks.items()},
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

        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, target_size)
        mask = (mask > 127).astype(np.float32)

        return image, mask


def build_lesion_segmentation_model(
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    num_lesion_classes: int = 1,
) -> Model:
    """Build U-Net style lesion segmentation model.

    Uses EfficientNetB0 encoder with decoder head.

    Args:
        input_shape: Input image shape.
        num_lesion_classes: Number of lesion types to segment.

    Returns:
        Keras Model for segmentation.
    """
    inputs = layers.Input(shape=input_shape)

    # Encoder (EfficientNetB0)
    encoder = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_tensor=inputs,
    )

    # Get skip connections from different levels
    skips = [
        encoder.get_layer("block2a_expand_activation").output,  # 56x56
        encoder.get_layer("block3a_expand_activation").output,  # 28x28
        encoder.get_layer("block4a_expand_activation").output,  # 14x14
        encoder.output,  # 7x7
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

    # Final upsampling to original size
    x = layers.UpSampling2D(size=(2, 2))(x)
    x = layers.Conv2D(16, 3, padding="same", activation="relu")(x)

    # Output
    outputs = layers.Conv2D(num_lesion_classes, 1, activation="sigmoid")(x)

    model = Model(inputs=inputs, outputs=outputs, name="lesion_segmentation")
    return model


def train_lesion_model(
    data_dir: str = "data/idrid",
    lesion_type: str = "microaneurysms",
    output_dir: str = "models/idrid",
    config_path: str = "configs/config.yaml",
) -> Tuple[Model, Dict[str, Any]]:
    """Train lesion segmentation model for a specific lesion type.

    Args:
        data_dir: IDRiD data directory.
        lesion_type: Which lesion type to train for.
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
    dataset = IDRiDLesionDataset(data_dir=data_dir, lesion_types=[lesion_type])
    info = dataset.load_data()

    print(f"Loaded {info['total_images']} images")
    print(f"Lesion masks available: {info['lesion_counts']}")

    if lesion_type not in dataset.masks or len(dataset.masks[lesion_type]) == 0:
        print(f"WARNING: No masks available for {lesion_type}")
        print(f"Available: {info['available_lesions']}")
        return None, {"status": "no_data", "lesion_type": lesion_type}

    # Build model
    model = build_lesion_segmentation_model(
        input_shape=(target_size[0], target_size[1], 3),
        num_lesion_classes=1,
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    print(f"Model built: {model.count_params():,} parameters")

    # Save model architecture
    model_json = model.to_json()
    with open(output_path / f"{lesion_type}_model_architecture.json", "w") as f:
        f.write(model_json)

    metadata = {
        "lesion_type": lesion_type,
        "model_name": f"lesion_{lesion_type}",
        "input_shape": config["image"]["size"],
        "total_images": info["total_images"],
        "status": "model_built_not_trained",
        "note": "Model architecture created. Train with actual IDRiD data.",
    }

    with open(output_path / f"{lesion_type}_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to {output_path / f'{lesion_type}_model_architecture.json'}")
    print("NOTE: Model is NOT TRAINED. Train with actual IDRiD dataset.")

    return model, metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train IDRiD lesion segmentation")
    parser.add_argument("--data-dir", default="data/idrid")
    parser.add_argument("--lesion", default="microaneurysms",
                       choices=IDRiDLesionDataset.LESION_TYPES)
    parser.add_argument("--output", default="models/idrid")
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()

    model, history = train_lesion_model(
        data_dir=args.data_dir,
        lesion_type=args.lesion,
        output_dir=args.output,
        config_path=args.config,
    )
