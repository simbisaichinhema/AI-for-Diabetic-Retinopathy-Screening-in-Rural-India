"""Vessel segmentation inference wrapper."""

import numpy as np
import cv2
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class VesselAnalyzer:
    """Wrapper for retinal vessel segmentation."""

    def __init__(self, model_path: str = "models/drive/vessel_model.keras"):
        self.model_path = Path(model_path)
        self.model = None
        self.available = False

    def load_model(self):
        """Load trained vessel segmentation model."""
        if self.model_path.exists():
            import tensorflow as tf
            self.model = tf.keras.models.load_model(str(self.model_path))
            self.available = True

    def segment(self, image: np.ndarray) -> Dict[str, Any]:
        """Segment retinal vessels.

        Args:
            image: Fundus image (H, W, 3).

        Returns:
            Dictionary with vessel segmentation results.
        """
        if not self.available or self.model is None:
            return {
                "available": False,
                "note": "Vessel model not trained. Train with DRIVE dataset.",
                "vessel_mask": None,
            }

        # Preprocess
        if image.dtype != np.float32:
            image = image.astype(np.float32) / 255.0

        # Add batch dimension
        input_tensor = np.expand_dims(image, axis=0)

        # Predict
        mask = self.model.predict(input_tensor, verbose=0)
        mask = (mask[0, :, :, 0] > 0.5).astype(np.uint8)

        # Compute metrics
        vessel_pixels = np.sum(mask)
        total_pixels = mask.shape[0] * mask.shape[1]
        coverage = vessel_pixels / total_pixels

        return {
            "available": True,
            "vessel_mask": mask,
            "coverage": float(coverage),
            "note": "Vessel segmentation is structural evidence, not a DR diagnosis.",
        }

    def generate_overlay(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        alpha: float = 0.5,
    ) -> np.ndarray:
        """Generate vessel overlay visualization."""
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                overlay = (image * 255).astype(np.uint8)
            else:
                overlay = image.astype(np.uint8)
        else:
            overlay = image.copy()

        # Create colored vessel mask
        vessel_overlay = np.zeros_like(overlay)
        vessel_overlay[mask > 0] = [0, 255, 0]  # Green for vessels

        # Blend
        result = cv2.addWeighted(overlay, 1 - alpha, vessel_overlay, alpha, 0)
        return result
