"""CORAL ordinal regression utilities and QWK cutoff search.

Adapted from the competitor's approach (khir00/Diabetic-Retinopathy) and integrated
into our pipeline. ORDINAL REGRESSION is superior to standard classification for
DR grading because grades are ordered (0 < 1 < 2 < 3 < 4).

Key insight: Instead of predicting 5 independent classes, predict 4 binary thresholds:
  "severity > 0", "severity > 1", "severity > 2", "severity > 3"
This respects the ordinal nature of DR grades and aligns with the QWK metric.
"""

import numpy as np
import tensorflow as tf
from sklearn.metrics import cohen_kappa_score
from typing import Tuple, Dict, Any, Optional


def label_to_ordinal(y):
    """Encode an integer grade (0..4) as 4 ordinal binary targets (y > k).

    Args:
        y: Integer labels (N,) with values 0-4.

    Returns:
        Ordinal targets (N, 4) as float32.
    """
    y = tf.cast(y, tf.int32)
    y = tf.expand_dims(y, axis=-1)  # (N,) -> (N, 1)
    thresholds = tf.range(4, dtype=tf.int32)  # (4,)
    return tf.cast(y > thresholds, tf.float32)  # (N, 4)


_bce = tf.keras.losses.BinaryCrossentropy(
    from_logits=True, reduction=tf.keras.losses.Reduction.NONE
)


@tf.function
def coral_loss(y_true, logits):
    """CORAL ordinal regression loss.

    Binary cross-entropy applied to each of the K-1 ordinal thresholds.
    Each threshold predicts P(grade > k).

    Args:
        y_true: Ordinal targets (N, K-1).
        logits: Raw logits (N, K-1) from the model.

    Returns:
        Per-sample loss (N,).
    """
    return _bce(y_true, logits)


def coral_loss_mean(y_true, logits):
    """Mean CORAL loss for training."""
    return tf.reduce_mean(coral_loss(y_true, logits))


def logits_to_prob(logits):
    """Convert raw logits to probabilities via sigmoid."""
    return 1.0 / (1.0 + np.exp(-logits))


def prob_to_continuous(prob):
    """Sum of threshold probabilities -> single continuous severity score.

    A higher score means more severe DR.
    """
    return prob.sum(axis=1)


def apply_cutoffs(cont, cutoffs):
    """Map continuous severity score to discrete grade 0..4 using 4 cutoffs.

    Args:
        cont: Continuous severity scores (N,).
        cutoffs: Tuple of 4 cutoffs (c0, c1, c2, c3).

    Returns:
        Predicted grades (N,) with values 0-4.
    """
    c0, c1, c2, c3 = cutoffs
    pred = np.zeros_like(cont, dtype=np.int32)
    pred += (cont > c0).astype(np.int32)
    pred += (cont > c1).astype(np.int32)
    pred += (cont > c2).astype(np.int32)
    pred += (cont > c3).astype(np.int32)
    return pred


def qwk(y_true, y_pred):
    """Quadratic Weighted Kappa — the APTOS competition metric.

    QWK penalizes large disagreements more than small ones,
    making it ideal for ordinal severity grading.
    """
    return cohen_kappa_score(y_true, y_pred, weights="quadratic")


def search_best_cutoffs(
    cont: np.ndarray,
    y_true: np.ndarray,
    iters: int = 4500,
    seed: int = 42,
    min_gap: float = 0.25,
    grid_range: Tuple[float, float] = (0.20, 3.81),
    grid_step: float = 0.05,
    distribution_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Tuple[float, Tuple[float, float, float, float]]:
    """Random search over 4 cutoffs, maximizing QWK under constraints.

    Args:
        cont: Continuous severity scores (N,).
        y_true: True labels (N,).
        iters: Number of random search iterations.
        seed: Random seed.
        min_gap: Minimum gap between adjacent cutoffs.
        grid_range: Range for cutoff grid.
        grid_step: Step size for cutoff grid.
        distribution_constraints: Optional constraints on predicted class proportions.

    Returns:
        (best_qwk, best_cutoffs)
    """
    rng = np.random.RandomState(seed)
    best = -1.0
    best_c = (0.8, 1.6, 2.4, 3.2)
    grid = np.arange(grid_range[0], grid_range[1], grid_step)
    n = len(y_true)

    # Default distribution constraints from APTOS validation proportions
    if distribution_constraints is None:
        distribution_constraints = {
            "p1": (0.05, 0.15),
            "p3": (0.03, 0.09),
            "p4": (0.05, 0.10),
        }

    for _ in range(iters):
        c = rng.choice(grid, size=4, replace=False)
        c.sort()

        # Enforce minimum gap between cutoffs
        if (c[1] - c[0] < min_gap) or (c[2] - c[1] < min_gap) or (c[3] - c[2] < min_gap):
            continue

        pred = apply_cutoffs(cont, tuple(c))

        # Check distribution constraints
        valid = True
        for cls, (p_min, p_max) in distribution_constraints.items():
            cls_idx = int(cls[1])  # "p1" -> 1, "p3" -> 3, "p4" -> 4
            p_actual = (pred == cls_idx).sum() / n
            if not (p_min <= p_actual <= p_max):
                valid = False
                break

        if not valid:
            continue

        score = qwk(y_true, pred)
        if score > best:
            best = score
            best_c = tuple(c)

    return best, best_c


class QWKCallback(tf.keras.callbacks.Callback):
    """Per-epoch QWK evaluation + best-checkpoint callback.

    After each epoch, searches for the best QWK cutoffs on the validation set
    and checkpoints weights + cutoffs whenever QWK improves.
    """

    def __init__(self, val_dataset, val_labels, out_dir="models/aptos"):
        super().__init__()
        self.val_dataset = val_dataset
        self.val_labels = val_labels
        self.out_dir = out_dir
        self.best_qwk = -1.0
        self.best_cutoffs = None
        self.history = {"train_loss": [], "val_loss": [], "val_qwk": []}

    def on_epoch_end(self, epoch, logs=None):
        import os
        logs = logs or {}
        self.history["train_loss"].append(float(logs.get("loss", np.nan)))
        self.history["val_loss"].append(float(logs.get("val_loss", np.nan)))

        # Get predictions on validation set
        logits = self.model.predict(self.val_dataset, verbose=0)
        prob = logits_to_prob(logits)
        cont = prob_to_continuous(prob)

        # Search for best cutoffs
        best_score, best_c = search_best_cutoffs(cont, self.val_labels)
        pred = apply_cutoffs(cont, best_c)

        self.history["val_qwk"].append(float(best_score))

        from sklearn.metrics import precision_recall_fscore_support
        prec, rec, f1, _ = precision_recall_fscore_support(
            self.val_labels, pred, average="macro", zero_division=0
        )

        print(f"\nEpoch {epoch+1} - Macro P/R/F1: {prec:.4f}/{rec:.4f}/{f1:.4f}")
        print(f"Epoch {epoch+1} - QWK: {best_score:.5f} | cutoffs={tuple(np.round(best_c, 2))}")

        if best_score > self.best_qwk:
            self.best_qwk = best_score
            self.best_cutoffs = best_c
            self.model.save_weights(os.path.join(self.out_dir, "best_qwk.weights.h5"))
            np.save(os.path.join(self.out_dir, "best_coral_cutoffs.npy"), np.array(best_c, dtype=np.float32))
            print(f"[CKPT] Saved BEST by QWK: {self.best_qwk:.5f}")
