"""Calibrated confidence display for DR predictions.

Raw softmax probability must NOT automatically be described as
reliable confidence. This module provides calibrated confidence scores.
"""

import numpy as np
from typing import Dict, Any, Optional


class CalibratedConfidence:
    """Manage calibrated confidence scores for predictions."""

    def __init__(self, method: str = "temperature"):
        self.method = method
        self.calibrator = None

    def load_calibrator(self, calibrator_path: str):
        """Load fitted calibrator from file."""
        import pickle
        with open(calibrator_path, "rb") as f:
            self.calibrator = pickle.load(f)

    def get_confidence(
        self,
        probabilities: np.ndarray,
        predicted_class: int,
        calibrated: bool = True,
    ) -> Dict[str, Any]:
        """Get confidence information for a prediction.

        Args:
            probabilities: Model output probabilities (N, C).
            predicted_class: Predicted class index.
            calibrated: Whether to use calibrated probabilities.

        Returns:
            Dictionary with confidence information.
        """
        raw_confidence = float(probabilities[0, predicted_class])

        # Get calibrated confidence if available
        if calibrated and self.calibrator is not None:
            calibrated_probs = self.calibrator.predict_proba(probabilities)
            cal_confidence = float(calibrated_probs[0, predicted_class])
        else:
            cal_confidence = raw_confidence

        # Confidence category
        if cal_confidence >= 0.9:
            category = "High"
            description = "Model is highly confident in this prediction."
        elif cal_confidence >= 0.7:
            category = "Moderate"
            description = "Model has moderate confidence. Clinical review recommended."
        elif cal_confidence >= 0.5:
            category = "Low"
            description = "Model has low confidence. Clinical review strongly recommended."
        else:
            category = "Uncertain"
            description = "Model is uncertain. Manual review required."

        return {
            "raw_confidence": round(raw_confidence, 4),
            "calibrated_confidence": round(cal_confidence, 4),
            "confidence_category": category,
            "description": description,
            "method": self.method if calibrated else "raw_softmax",
            "note": (
                "Confidence scores are model-derived estimates, not clinical probabilities. "
                "They should not be interpreted as diagnostic certainty."
            ),
        }

    def format_confidence(self, confidence_info: Dict[str, Any]) -> str:
        """Format confidence for display."""
        return (
            f"Calibrated Confidence: {confidence_info['calibrated_confidence']:.1%}\n"
            f"Category: {confidence_info['confidence_category']}\n"
            f"{confidence_info['description']}"
        )
