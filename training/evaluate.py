"""General evaluation metrics for classification tasks.

Provides reusable metric computation functions.
"""

import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score,
    classification_report,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probs: Optional[np.ndarray] = None,
    class_names: Optional[List[str]] = None,
    average: str = "macro",
) -> Dict[str, Any]:
    """Compute comprehensive classification metrics.

    Args:
        y_true: True labels.
        y_pred: Predicted labels.
        y_probs: Probability matrix (optional, for AUROC).
        class_names: List of class names.
        average: Averaging method for multi-class metrics.

    Returns:
        Dictionary of metrics.
    """
    metrics = {}

    # Accuracy
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))

    # Precision, Recall, F1
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )

    # Overall averages
    for avg in ["macro", "weighted"]:
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, average=avg, zero_division=0
        )
        metrics[f"{avg}_precision"] = float(p)
        metrics[f"{avg}_recall"] = float(r)
        metrics[f"{avg}_f1"] = float(f)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = cm.tolist()

    # Per-class metrics
    if class_names is not None:
        metrics["per_class"] = {}
        for i, name in enumerate(class_names):
            if i < len(precision):
                metrics["per_class"][name] = {
                    "precision": float(precision[i]),
                    "recall": float(recall[i]),
                    "f1": float(f1[i]),
                    "support": int(support[i]),
                }

    # AUROC
    if y_probs is not None:
        try:
            if y_probs.ndim == 1:
                # Binary case
                metrics["auroc"] = float(roc_auc_score(y_true, y_probs))
            else:
                # Multi-class
                metrics["auroc_macro"] = float(
                    roc_auc_score(y_true, y_probs, multi_class="ovr", average="macro")
                )
                metrics["auroc_weighted"] = float(
                    roc_auc_score(y_true, y_probs, multi_class="ovr", average="weighted")
                )
        except ValueError:
            pass

    # Classification report
    if class_names is not None:
        metrics["classification_report"] = classification_report(
            y_true, y_pred,
            target_names=class_names[:len(np.unique(y_true))],
            output_dict=True,
            zero_division=0,
        )

    return metrics


def compute_calibration_metrics(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, float]:
    """Compute calibration metrics.

    Args:
        y_true: True labels.
        y_probs: Predicted probabilities.
        n_bins: Number of bins for ECE.

    Returns:
        Dictionary with ECE, Brier score, and calibration curve data.
    """
    # Get max probability per sample (confidence)
    if y_probs.ndim > 1:
        confidences = np.max(y_probs, axis=1)
        predictions = np.argmax(y_probs, axis=1)
    else:
        confidences = y_probs
        predictions = (y_probs > 0.5).astype(int)

    # Binary accuracy
    correct = (predictions == y_true).astype(float)

    # Brier score
    if y_probs.ndim > 1:
        n_classes = y_probs.shape[1]
        y_true_onehot = np.eye(n_classes)[y_true]
        brier = float(np.mean(np.sum((y_probs - y_true_onehot) ** 2, axis=1)))
    else:
        brier = float(np.mean((y_probs - y_true) ** 2))

    # Expected Calibration Error (ECE)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    calibration_curve = []

    for i in range(n_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            avg_confidence = np.mean(confidences[in_bin])
            avg_accuracy = np.mean(correct[in_bin])
            ece += prop_in_bin * abs(avg_accuracy - avg_confidence)

            calibration_curve.append({
                "bin_lower": float(bin_boundaries[i]),
                "bin_upper": float(bin_boundaries[i + 1]),
                "mean_confidence": float(avg_confidence),
                "mean_accuracy": float(avg_accuracy),
                "count": int(np.sum(in_bin)),
            })

    return {
        "ece": float(ece),
        "brier_score": brier,
        "n_bins": n_bins,
        "calibration_curve": calibration_curve,
    }
