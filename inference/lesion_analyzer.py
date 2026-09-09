"""Lesion analysis inference wrapper."""

import numpy as np
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from explainability.lesion_evidence import analyze_lesions, generate_lesion_overlay


class LesionAnalyzer:
    """Wrapper for lesion detection/segmentation."""

    def __init__(self, models_dir: str = "models/idrid"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.available = False

    def load_models(self):
        """Load trained lesion models."""
        # Check if any models are available
        for lesion_type in ["microaneurysms", "hemorrhages", "hard_exudates", "soft_exudates"]:
            model_path = self.models_dir / f"{lesion_type}_model.keras"
            if model_path.exists():
                import tensorflow as tf
                self.models[lesion_type] = tf.keras.models.load_model(str(model_path))
                self.available = True

    def analyze(
        self,
        image: np.ndarray,
        model_predictions: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Analyze lesions in an image.

        Args:
            image: Fundus image (H, W, 3).
            model_predictions: Optional model predictions per lesion type.

        Returns:
            Lesion analysis results.
        """
        # Use model predictions if no custom analysis needed
        return analyze_lesions(
            image,
            lesion_masks=None,
            model_predictions=model_predictions,
        )

    def generate_overlay(
        self,
        image: np.ndarray,
        lesion_masks: Optional[Dict[str, np.ndarray]] = None,
    ) -> np.ndarray:
        """Generate lesion overlay visualization."""
        if lesion_masks is None:
            lesion_masks = {}
        return generate_lesion_overlay(image, lesion_masks)
