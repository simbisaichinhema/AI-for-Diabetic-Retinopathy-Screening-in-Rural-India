#!/usr/bin/env python3
"""Run APTOS training with sample data for pipeline verification."""

import sys
import os
import yaml

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from training.aptos_dataset import load_and_split_aptos
from training.train_aptos import train_aptos_classifier


def main():
    # Load config
    with open("configs/config.yaml") as f:
        config = yaml.safe_load(f)

    # Reduce epochs for sample data
    config["training"]["epochs"] = 5
    config["training"]["fine_tune_epochs"] = 3
    config["training"]["patience"] = 3

    tmp_config = "/tmp/config_sample.yaml"
    with open(tmp_config, "w") as f:
        yaml.dump(config, f)

    # Load data
    print("=" * 50)
    print("PHASE 2: APTOS Classifier Training")
    print("=" * 50)

    loader, train_df, val_df, test_df = load_and_split_aptos(config_path=tmp_config)
    class_weights = loader.get_class_weights()

    print(f"\nClass weights: {class_weights}")
    print(f"\nStarting training...")

    # Train
    model, history = train_aptos_classifier(
        train_df=train_df,
        val_df=val_df,
        config_path=tmp_config,
        output_dir="models/aptos",
        class_weights=class_weights,
    )

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)
    print(f"Model: models/aptos/aptos_dr_classifier.keras")
    print(f"SavedModel: models/aptos/saved_model/")
    print(f"Total epochs: {len(history.get('loss', []))}")
    if history.get('val_accuracy'):
        print(f"Final val accuracy: {history['val_accuracy'][-1]:.4f}")


if __name__ == "__main__":
    main()
