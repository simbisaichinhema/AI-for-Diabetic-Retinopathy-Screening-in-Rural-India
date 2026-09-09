"""Probability calibration for DR classifier.

Implements temperature scaling and Platt scaling for
calibrating raw softmax probabilities.

Raw softmax probability must NOT automatically be described as
reliable confidence. Calibration improves this.
"""

import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from typing import Tuple, Optional, Dict, Any


class CalibratedClassifier:
    """Wrapper for calibrating classifier probabilities.

    Supports:
    - Temperature scaling
    - Platt scaling (sigmoid)
    - Isotonic regression
    """

    def __init__(self, method: str = "temperature"):
        """Initialize calibrator.

        Args:
            method: Calibration method ('temperature', 'platt', 'isotonic').
        """
        self.method = method
        self.params = None
        self.fitted = False

    def fit(
        self,
        logits: np.ndarray,
        y_true: np.ndarray,
        method: Optional[str] = None,
    ) -> "CalibratedClassifier":
        """Fit calibration parameters on validation set.

        Args:
            logits: Raw model outputs (N, C) before softmax.
            y_true: True labels (N,).
            method: Override calibration method.

        Returns:
            self
        """
        method = method or self.method

        if method == "temperature":
            self.params = self._fit_temperature(logits, y_true)
        elif method == "platt":
            self.params = self._fit_platt(logits, y_true)
        elif method == "isotonic":
            self.params = self._fit_isotonic(logits, y_true)
        else:
            raise ValueError(f"Unknown calibration method: {method}")

        self.fitted = True
        return self

    def predict_proba(self, logits: np.ndarray) -> np.ndarray:
        """Apply calibration to logits and return calibrated probabilities.

        Args:
            logits: Raw model outputs (N, C).

        Returns:
            Calibrated probabilities (N, C).
        """
        if not self.fitted:
            raise RuntimeError("Calibrator not fitted. Call fit() first.")

        if self.method == "temperature":
            T = self.params["temperature"]
            scaled_logits = logits / T
            return softmax(scaled_logits, axis=1)

        elif self.method == "platt":
            a = self.params["a"]
            b = self.params["b"]
            probs = softmax(logits, axis=1)
            # Apply sigmoid scaling to each class
            scaled = 1.0 / (1.0 + np.exp(-a * probs + b))
            # Renormalize
            return scaled / scaled.sum(axis=1, keepdims=True)

        elif self.method == "isotonic":
            probs = softmax(logits, axis=1)
            calibrated = np.zeros_like(probs)
            for c in range(probs.shape[1]):
                calibrator = self.params.get(f"class_{c}")
                if calibrator is not None:
                    calibrated[:, c] = calibrator.predict(probs[:, c])
                else:
                    calibrated[:, c] = probs[:, c]
            # Ensure valid probabilities
            calibrated = np.clip(calibrated, 0, None)
            calibrated /= calibrated.sum(axis=1, keepdims=True) + 1e-10
            return calibrated

    def _fit_temperature(self, logits: np.ndarray, y_true: np.ndarray) -> dict:
        """Fit temperature scaling parameter."""
        n_classes = logits.shape[1]

        def loss(T):
            scaled = logits / T
            probs = softmax(scaled, axis=1)
            # Negative log-likelihood
            log_probs = np.log(probs + 1e-10)
            return -np.mean(log_probs[np.arange(len(y_true)), y_true])

        # Optimize temperature
        result = minimize(loss, x0=1.0, method="Nelder-Mead", bounds=[(0.1, 10.0)])
        return {"temperature": float(result.x[0])}

    def _fit_platt(self, logits: np.ndarray, y_true: np.ndarray) -> dict:
        """Fit Platt scaling parameters."""
        probs = softmax(logits, axis=1)
        n_classes = probs.shape[1]

        # For multi-class, fit one-vs-rest
        best_a, best_b = 1.0, 0.0
        best_loss = float("inf")

        for a_init in [0.5, 1.0, 2.0]:
            for b_init in [-1.0, 0.0, 1.0]:
                def loss_fn(params):
                    a, b = params
                    scaled = 1.0 / (1.0 + np.exp(-a * probs + b))
                    scaled = scaled / scaled.sum(axis=1, keepdims=True)
                    log_probs = np.log(scaled + 1e-10)
                    return -np.mean(log_probs[np.arange(len(y_true)), y_true])

                result = minimize(loss_fn, x0=[a_init, b_init], method="Nelder-Mead")
                if result.fun < best_loss:
                    best_loss = result.fun
                    best_a, best_b = result.x

        return {"a": float(best_a), "b": float(best_b)}

    def _fit_isotonic(self, logits: np.ndarray, y_true: np.ndarray) -> dict:
        """Fit isotonic regression for each class."""
        from sklearn.isotonic import IsotonicRegression

        probs = softmax(logits, axis=1)
        n_classes = probs.shape[1]
        params = {}

        for c in range(n_classes):
            binary_true = (y_true == c).astype(float)
            ir = IsotonicRegression(out_of_bounds="clip")
            ir.fit(probs[:, c], binary_true)
            params[f"class_{c}"] = ir

        return params


def calibrate_probabilities(
    logits: np.ndarray,
    y_true: np.ndarray,
    method: str = "temperature",
) -> Tuple[CalibratedClassifier, np.ndarray]:
    """Calibrate model probabilities.

    Args:
        logits: Raw model outputs (N, C).
        y_true: True labels (N,).
        method: Calibration method.

    Returns:
        (fitted_calibrator, calibrated_probabilities)
    """
    calibrator = CalibratedClassifier(method=method)
    calibrator.fit(logits, y_true)
    calibrated_probs = calibrator.predict_proba(logits)
    return calibrator, calibrated_probs


def compute_calibration_curve(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, Any]:
    """Compute reliability diagram data.

    Args:
        y_true: True labels.
        y_probs: Predicted probabilities (N, C).
        n_bins: Number of bins.

    Returns:
        Calibration curve data for plotting.
    """
    confidences = np.max(y_probs, axis=1)
    predictions = np.argmax(y_probs, axis=1)
    correct = (predictions == y_true).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bins = []

    for i in range(n_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        count = np.sum(in_bin)

        if count > 0:
            bins.append({
                "bin_lower": float(bin_boundaries[i]),
                "bin_upper": float(bin_boundaries[i + 1]),
                "mean_confidence": float(np.mean(confidences[in_bin])),
                "mean_accuracy": float(np.mean(correct[in_bin])),
                "count": int(count),
            })

    return {"bins": bins, "n_bins": n_bins}
