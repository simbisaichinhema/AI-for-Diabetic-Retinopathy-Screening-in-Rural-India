"""Cross-dataset validation for generalization assessment.

Evaluates model trained on APTOS on external datasets like Messidor-2.
DO NOT tune the final model on external datasets.
"""

import os
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

import tensorflow as tf
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.evaluate_aptos import load_trained_model, get_predictions
from training.train_aptos import create_tf_dataset


def load_messidor2_data(
    data_dir: str = "data/messidor2",
    label_mapping: Optional[Dict] = None,
) -> pd.DataFrame:
    """Load Messidor-2 dataset for external validation.

    NOTE: Verify labels and usage terms before implementation.
    Messidor-2 has R0-R3 retinopathy grades, which may map differently
    to the 0-4 DR scale used in APTOS.

    Args:
        data_dir: Path to Messidor-2 data.
        label_mapping: Mapping from Messidor-2 labels to DR grades.

    Returns:
        DataFrame compatible with the evaluation pipeline.
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(
            f" Messidor-2 data not found at {data_path}.\n"
            f"Download from: http://www.adris.net/messidor2\n"
            f"Registration required for access."
        )

    # Default mapping: R0=0, R1=1, R2=2, R3=3
    # This is approximate and must be verified with actual Messidor-2 labels
    if label_mapping is None:
        label_mapping = {
            "R0": 0, "R1": 1, "R2": 2, "R3": 3,
            0: 0, 1: 1, 2: 2, 3: 3,
        }

    # Look for CSV or annotation file
    csv_files = list(data_path.glob("*.csv"))
    if csv_files:
        df = pd.read_csv(csv_files[0])
    else:
        # Try to find images and create DataFrame from folder structure
        image_files = list(data_path.glob("**/*.png")) + list(data_path.glob("**/*.jpg"))
        if not image_files:
            raise FileNotFoundError(f"No images found in {data_path}")

        df = pd.DataFrame({
            "image_path": [str(f) for f in image_files],
            "id_code": [f.stem for f in image_files],
        })

    return df


def cross_validate(
    model_path: str = "models/aptos/aptos_dr_classifier.keras",
    external_data_dir: str = "data/messidor2",
    config_path: str = "configs/config.yaml",
    output_dir: str = "reports",
    dataset_name: str = "messidor2",
) -> Dict[str, Any]:
    """Run cross-dataset validation.

    IMPORTANT: This evaluates generalization only.
    The model must NOT be tuned on the external dataset.

    Args:
        model_path: Path to trained APTOS model.
        external_data_dir: Path to external dataset.
        config_path: Config file path.
        output_dir: Directory to save results.
        dataset_name: Name of the external dataset.

    Returns:
        Evaluation results on external dataset.
    """
    # Load model
    model = load_trained_model(model_path)
    print(f"Loaded model from {model_path}")

    # Load external data
    try:
        external_df = load_messidor2_data(external_data_dir)
    except FileNotFoundError as e:
        print(f"\nWARNING: {e}")
        print("Cross-dataset validation skipped.")
        return {"status": "skipped", "reason": str(e)}

    print(f"Loaded {len(external_df)} images from {dataset_name}")

    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    batch_size = config["training"]["batch_size"]
    target_size = tuple(config["image"]["size"])

    # Create dataset
    # NOTE: For Messidor-2, we need to adapt the label loading
    # This is a placeholder that needs actual label integration
    if "diagnosis" not in external_df.columns:
        print("WARNING: External dataset labels not found.")
        print("Please provide labels in 'diagnosis' column.")
        return {"status": "skipped", "reason": "Labels not available"}

    eval_ds = create_tf_dataset(
        external_df, batch_size=batch_size, target_size=target_size, shuffle=False
    )

    # Get predictions
    y_true, y_pred, y_probs = get_predictions(model, eval_ds)

    # Compute metrics
    accuracy = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)

    class_names = {
        0: "No DR", 1: "Mild DR", 2: "Moderate DR",
        3: "Severe DR", 4: "Proliferative DR",
    }

    report = classification_report(
        y_true, y_pred,
        target_names=[class_names.get(i, f"Class {i}") for i in sorted(np.unique(y_true))],
        output_dict=True,
        zero_division=0,
    )

    results = {
        "dataset": dataset_name,
        "model_path": model_path,
        "num_samples": len(external_df),
        "accuracy": float(accuracy),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "note": (
            "External validation on Messidor-2. Model was NOT tuned on this dataset. "
            "Results assess generalization, not clinical performance."
        ),
    }

    # Print summary
    print(f"\n=== Cross-Dataset Validation: {dataset_name} ===")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Note: This is generalization assessment, not clinical validation.")

    # Save report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / f"cross_validation_{dataset_name}.json"

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=float)

    print(f"Report saved to {report_path}")

    return results
