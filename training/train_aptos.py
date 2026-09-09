"""APTOS DR classifier training pipeline.

Builds and trains a transfer-learning-based DR severity classifier.
Uses EfficientNetB0 as backbone with progressive fine-tuning.

Outputs:
- Trained model: models/aptos/aptos_dr_classifier.keras
- SavedModel: models/aptos/saved_model/
- Training history, configuration, and metadata.
"""

import os
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint,
    CSVLogger,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.aptos_dataset import AptosDataLoader
from preprocessing.transforms import preprocess_for_model


def build_aptos_classifier(
    num_classes: int = 5,
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.3,
    learning_rate: float = 0.001,
    freeze_backbone: bool = True,
) -> Model:
    """Build EfficientNetB0-based DR classifier.

    Architecture:
        Input -> EfficientNetB0 (pretrained) -> GlobalAvgPool
        -> Dropout -> Dense(num_classes, softmax)

    Args:
        num_classes: Number of DR grades (0-4 = 5 classes).
        input_shape: Input image shape.
        dropout_rate: Dropout rate for regularization.
        learning_rate: Initial learning rate.
        freeze_backbone: Whether to freeze pretrained backbone weights.

    Returns:
        Compiled Keras Model.
    """
    # Input
    inputs = layers.Input(shape=input_shape, name="input_image")

    # Backbone
    backbone = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_tensor=inputs,
        pooling=None,
    )

    # Freeze backbone if requested
    if freeze_backbone:
        for layer in backbone.layers:
            layer.trainable = False

    # Classification head
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(backbone.output)
    x = layers.BatchNormalization(name="bn")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = Model(inputs=inputs, outputs=outputs, name="aptos_dr_classifier")

    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def create_tf_dataset(
    df: pd.DataFrame,
    batch_size: int = 32,
    target_size: Tuple[int, int] = (224, 224),
    shuffle: bool = True,
    augment: bool = False,
    seed: int = 42,
) -> tf.data.Dataset:
    """Create a tf.data.Dataset from a DataFrame.

    Args:
        df: DataFrame with 'image_path' and 'diagnosis' columns.
        batch_size: Batch size.
        target_size: Target image size (H, W).
        shuffle: Whether to shuffle.
        augment: Whether to apply augmentation.
        seed: Random seed.

    Returns:
        tf.data.Dataset
    """
    image_paths = df["image_path"].values
    labels = df["diagnosis"].values.astype(np.int32)

    def load_and_preprocess(path, label):
        # Read image
        image = tf.io.read_file(path)
        image = tf.image.decode_png(image, channels=3)
        image = tf.image.resize(image, target_size)
        image = tf.cast(image, tf.float32) / 255.0

        # ImageNet normalization
        mean = tf.constant([0.485, 0.456, 0.406])
        std = tf.constant([0.229, 0.224, 0.225])
        image = (image - mean) / std

        return image, label

    dataset = tf.data.Dataset.from_tensor_slices((image_paths, labels))
    dataset = dataset.map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)

    if shuffle:
        dataset = dataset.shuffle(buffer_size=1000, seed=seed)

    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


def train_aptos_classifier(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    config_path: str = "configs/config.yaml",
    output_dir: str = "models/aptos",
    class_weights: Optional[Dict[int, float]] = None,
) -> Tuple[Model, Dict[str, Any]]:
    """Full APTOS training pipeline with progressive fine-tuning.

    Phase 1: Train classification head (backbone frozen)
    Phase 2: Fine-tune upper backbone layers

    Args:
        train_df: Training DataFrame.
        val_df: Validation DataFrame.
        config_path: Path to config YAML.
        output_dir: Directory to save model and artifacts.
        class_weights: Optional class weights for imbalanced data.

    Returns:
        (trained_model, training_history)
    """
    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    batch_size = config["training"]["batch_size"]
    target_size = tuple(config["image"]["size"])
    seed = config["project"]["seed"]

    # Create datasets
    train_ds = create_tf_dataset(
        train_df, batch_size=batch_size, target_size=target_size,
        shuffle=True, seed=seed,
    )
    val_ds = create_tf_dataset(
        val_df, batch_size=batch_size, target_size=target_size,
        shuffle=False, seed=seed,
    )

    # Build model
    model = build_aptos_classifier(
        num_classes=5,
        input_shape=(target_size[0], target_size[1], 3),
        learning_rate=config["training"]["learning_rate"],
        freeze_backbone=True,
    )

    print(f"Model built: {model.count_params():,} parameters")
    print(f"Trainable parameters: {sum(np.prod(p.shape) for p in model.trainable_weights):,}")

    # Callbacks
    callbacks_phase1 = [
        EarlyStopping(
            monitor="val_loss",
            patience=config["training"]["patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=config["training"]["min_lr"],
            verbose=1,
        ),
        ModelCheckpoint(
            str(output_path / "best_phase1.keras"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        CSVLogger(str(output_path / "training_log_phase1.csv")),
    ]

    # Phase 1: Train classification head
    print("\n=== Phase 1: Training classification head ===")
    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["training"]["epochs"],
        callbacks=callbacks_phase1,
        class_weight=class_weights,
        verbose=1,
    )

    # Phase 2: Fine-tune upper backbone
    print("\n=== Phase 2: Fine-tuning upper backbone ===")

    # Find the EfficientNetB0 backbone by name
    backbone = None
    for layer in model.layers:
        if hasattr(layer, 'name') and 'efficient_net' in layer.name.lower():
            backbone = layer
            break
        if hasattr(layer, 'layers'):  # It's a nested model
            for sublayer in layer.layers:
                if hasattr(sublayer, 'name') and 'efficient' in sublayer.name.lower():
                    backbone = layer
                    break
            if backbone:
                break

    if backbone is None:
        # Fallback: unfreeze all layers in the model
        print("Could not find backbone by name, unfreezing all layers")
        for layer in model.layers:
            layer.trainable = True
    else:
        print(f"Found backbone: {backbone.name}")
        backbone.trainable = True

        # In Keras 3, enumerate all nested layers
        all_layers = []
        def collect_layers(l):
            if hasattr(l, 'layers'):
                for sub in l.layers:
                    collect_layers(sub)
            else:
                all_layers.append(l)
        collect_layers(backbone)

        # Freeze all but last 30 layers
        if len(all_layers) > 30:
            for layer in all_layers[:-30]:
                layer.trainable = False
            print(f"Froze {len(all_layers)-30} layers, unfroze last 30")

    # Recompile with lower learning rate
    model.compile(
        optimizer=keras.optimizers.Adam(
            learning_rate=config["training"]["fine_tune_lr"]
        ),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print(f"Trainable params after unfreezing: {sum(np.prod(p.shape) for p in model.trainable_weights):,}")

    callbacks_phase2 = [
        EarlyStopping(
            monitor="val_loss",
            patience=config["training"]["patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=config["training"]["min_lr"],
            verbose=1,
        ),
        ModelCheckpoint(
            str(output_path / "aptos_dr_classifier.keras"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        CSVLogger(str(output_path / "training_log_phase2.csv")),
    ]

    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["training"]["fine_tune_epochs"],
        callbacks=callbacks_phase2,
        class_weight=class_weights,
        verbose=1,
    )

    # Save final model in multiple formats
    model.save(str(output_path / "aptos_dr_classifier.keras"))

    # Save as SavedModel for MATLAB compatibility (Keras 3 uses export())
    savedmodel_path = output_path / "saved_model"
    try:
        model.export(str(savedmodel_path))
    except Exception as e:
        print(f"SavedModel export skipped: {e}")
        print("The .keras model is available for inference.")

    # Save class names and config
    class_names = {
        0: "No DR", 1: "Mild DR", 2: "Moderate DR",
        3: "Severe DR", 4: "Proliferative DR",
    }

    metadata = {
        "model_name": "aptos_dr_classifier",
        "architecture": "EfficientNetB0",
        "num_classes": 5,
        "class_names": class_names,
        "input_shape": config["image"]["size"],
        "training_date": datetime.now().isoformat(),
        "config": config["training"],
        "seed": seed,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "phase1_epochs_run": len(history1.history["loss"]),
        "phase2_epochs_run": len(history2.history["loss"]),
    }

    with open(output_path / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # Combine training histories
    combined_history = {}
    for key in history1.history:
        combined_history[key] = history1.history[key] + history2.history[key]

    with open(output_path / "training_history.json", "w") as f:
        json.dump(combined_history, f, indent=2, default=float)

    print(f"\nModel saved to {output_path}")
    print(f"  - aptos_dr_classifier.keras")
    print(f"  - saved_model/ (TensorFlow SavedModel)")

    return model, combined_history


if __name__ == "__main__":
    import argparse
    from training.aptos_dataset import load_and_split_aptos

    parser = argparse.ArgumentParser(description="Train APTOS DR classifier")
    parser.add_argument("--data-dir", default="data/aptos", help="APTOS data directory")
    parser.add_argument("--config", default="configs/config.yaml", help="Config file path")
    parser.add_argument("--output", default="models/aptos", help="Output directory")
    args = parser.parse_args()

    # Load and split data
    loader, train_df, val_df, test_df = load_and_split_aptos(
        data_dir=args.data_dir,
        config_path=args.config,
    )

    # Get class weights
    class_weights = loader.get_class_weights()
    print(f"Class weights: {class_weights}")

    # Train
    model, history = train_aptos_classifier(
        train_df=train_df,
        val_df=val_df,
        config_path=args.config,
        output_dir=args.output,
        class_weights=class_weights,
    )

    print("\nTraining complete!")
