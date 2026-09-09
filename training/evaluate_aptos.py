"""APTOS DR classifier evaluation pipeline.

Evaluates:
- 5-class DR severity (Grade 0-4)
- Binary referable DR (Level 2+)
- Per-class metrics
- Calibration analysis
"""

import os
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import tensorflow as tf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_fscore_support,
    accuracy_score,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.aptos_dataset import AptosDataLoader
from training.train_aptos import create_tf_dataset


def load_trained_model(model_path: str = "models/aptos/aptos_dr_classifier.keras") -> tf.keras.Model:
    """Load trained APTOS classifier."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Train the model first.")
    return tf.keras.models.load_model(model_path)


def get_predictions(
    model: tf.keras.Model,
    dataset: tf.data.Dataset,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Get model predictions for a dataset.

    Returns:
        (true_labels, predicted_labels, probability_matrix)
    """
    all_labels = []
    all_preds = []
    all_probs = []

    for batch_images, batch_labels in dataset:
        probs = model.predict(batch_images, verbose=0)
        preds = np.argmax(probs, axis=1)

        all_labels.extend(batch_labels.numpy())
        all_preds.extend(preds)
        all_probs.extend(probs)

    return np.array(all_labels), np.array(all_preds), np.array(all_probs)


def evaluate_5class(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray,
    class_names: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """Evaluate 5-class DR severity classification.

    Args:
        y_true: True labels (0-4).
        y_pred: Predicted labels (0-4).
        y_probs: Probability matrix (N, 5).
        class_names: Optional mapping of class index to name.

    Returns:
        Dictionary with all evaluation metrics.
    """
    if class_names is None:
        class_names = {
            0: "No DR", 1: "Mild DR", 2: "Moderate DR",
            3: "Severe DR", 4: "Proliferative DR",
        }

    # Basic metrics
    accuracy = accuracy_score(y_true, y_pred)

    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=range(5), zero_division=0
    )

    # Macro and weighted averages
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=range(5))

    # AUROC (one-vs-rest)
    try:
        auroc = roc_auc_score(y_true, y_probs, multi_class="ovr", average="macro")
    except ValueError:
        auroc = None

    # Per-class AUROC
    per_class_auroc = {}
    for i in range(5):
        try:
            binary_true = (y_true == i).astype(int)
            per_class_auroc[class_names[i]] = roc_auc_score(binary_true, y_probs[:, i])
        except ValueError:
            per_class_auroc[class_names[i]] = None

    # Classification report
    report = classification_report(
        y_true, y_pred, target_names=[class_names[i] for i in range(5)],
        output_dict=True, zero_division=0,
    )

    return {
        "accuracy": float(accuracy),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_precision),
        "weighted_recall": float(weighted_recall),
        "weighted_f1": float(weighted_f1),
        "auroc_macro": float(auroc) if auroc is not None else None,
        "per_class_auroc": per_class_auroc,
        "confusion_matrix": cm.tolist(),
        "per_class_metrics": {
            class_names[i]: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in range(5)
        },
        "classification_report": report,
    }


def evaluate_referable_dr(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: np.ndarray,
    threshold: int = 2,
) -> Dict[str, Any]:
    """Evaluate binary referable DR detection.

    Referable DR is defined as Level >= threshold (default: 2).
    This is a PROJECT DEFINITION for SIH, not a clinical standard.

    Args:
        y_true: True labels (0-4).
        y_pred: Predicted labels (0-4).
        y_probs: Probability matrix (N, 5).
        threshold: Minimum level for referable DR.

    Returns:
        Dictionary with binary evaluation metrics.
    """
    # Convert to binary
    y_true_binary = (y_true >= threshold).astype(int)
    y_pred_binary = (y_pred >= threshold).astype(int)

    # Probability of referable: sum probabilities for classes >= threshold
    y_prob_binary = np.sum(y_probs[:, threshold:], axis=1)

    # Metrics
    accuracy = accuracy_score(y_true_binary, y_pred_binary)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_binary, y_pred_binary, average="binary", zero_division=0
    )

    # Confusion matrix
    cm = confusion_matrix(y_true_binary, y_pred_binary, labels=[0, 1])

    # AUROC
    try:
        auroc = roc_auc_score(y_true_binary, y_prob_binary)
    except ValueError:
        auroc = None

    # Sensitivity and specificity
    tn, fp, fn, tp = cm.ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "threshold": threshold,
        "threshold_label": f"Level {threshold}+",
        "accuracy": float(accuracy),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auroc": float(auroc) if auroc is not None else None,
        "confusion_matrix": cm.tolist(),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "note": "Level 2+ referable DR is a project definition for SIH, not a clinical standard.",
    }


def evaluate_aptos_classifier(
    model_path: str = "models/aptos/aptos_dr_classifier.keras",
    data_dir: str = "data/aptos",
    config_path: str = "configs/config.yaml",
    output_dir: str = "reports",
    split: str = "test",
) -> Dict[str, Any]:
    """Full evaluation of APTOS classifier on a dataset split.

    Args:
        model_path: Path to trained model.
        data_dir: APTOS data directory.
        config_path: Config file path.
        output_dir: Directory to save evaluation report.
        split: Which split to evaluate ('train', 'val', or 'test').

    Returns:
        Complete evaluation metrics dictionary.
    """
    # Load model
    model = load_trained_model(model_path)
    print(f"Loaded model from {model_path}")

    # Load data
    loader = AptosDataLoader(data_dir=data_dir, config_path=config_path)
    loader.load_data()
    loader.split()

    if split == "train":
        eval_df = loader.train_df
    elif split == "val":
        eval_df = loader.val_df
    else:
        eval_df = loader.test_df

    print(f"Evaluating on {split} set: {len(eval_df)} images")

    # Create dataset
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    batch_size = config["training"]["batch_size"]
    target_size = tuple(config["image"]["size"])

    eval_ds = create_tf_dataset(
        eval_df, batch_size=batch_size, target_size=target_size, shuffle=False
    )

    # Get predictions
    y_true, y_pred, y_probs = get_predictions(model, eval_ds)

    # Evaluate
    class_names = {
        0: "No DR", 1: "Mild DR", 2: "Moderate DR",
        3: "Severe DR", 4: "Proliferative DR",
    }

    metrics_5class = evaluate_5class(y_true, y_pred, y_probs, class_names)
    metrics_referable = evaluate_referable_dr(y_true, y_pred, y_probs)

    # Combine
    results = {
        "model_path": model_path,
        "split": split,
        "num_samples": len(eval_df),
        "five_class": metrics_5class,
        "referable_dr": metrics_referable,
    }

    # Print summary
    print(f"\n=== 5-Class DR Evaluation ({split}) ===")
    print(f"Accuracy: {metrics_5class['accuracy']:.4f}")
    print(f"Macro F1: {metrics_5class['macro_f1']:.4f}")
    print(f"Macro AUROC: {metrics_5class.get('auroc_macro', 'N/A')}")

    print(f"\n=== Referable DR Evaluation (Level 2+) ===")
    print(f"Sensitivity: {metrics_referable['sensitivity']:.4f}")
    print(f"Specificity: {metrics_referable['specificity']:.4f}")
    print(f"F1: {metrics_referable['f1']:.4f}")
    print(f"AUROC: {metrics_referable.get('auroc', 'N/A')}")

    # Check SIH targets
    print(f"\n=== SIH Targets ===")
    target_sens = 0.90
    target_spec = 0.85
    actual_sens = metrics_referable['sensitivity']
    actual_spec = metrics_referable['specificity']

    print(f"Sensitivity: {actual_sens:.4f} (target: {target_sens}) {'✓' if actual_sens >= target_sens else '✗'}")
    print(f"Specificity: {actual_spec:.4f} (target: {target_spec}) {'✓' if actual_spec >= target_spec else '✗'}")

    if actual_sens < target_sens or actual_spec < target_spec:
        print("\nNOTE: SIH targets are goals, not claims. Results may vary.")
        print("Never claim target achievement unless actual held-out evaluation demonstrates it.")

    # Save report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_path = output_path / f"evaluation_{split}.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=float)

    print(f"\nEvaluation report saved to {report_path}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate APTOS DR classifier")
    parser.add_argument("--model", default="models/aptos/aptos_dr_classifier.keras")
    parser.add_argument("--data-dir", default="data/aptos")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--output", default="reports")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    args = parser.parse_args()

    results = evaluate_aptos_classifier(
        model_path=args.model,
        data_dir=args.data_dir,
        config_path=args.config,
        output_dir=args.output,
        split=args.split,
    )
