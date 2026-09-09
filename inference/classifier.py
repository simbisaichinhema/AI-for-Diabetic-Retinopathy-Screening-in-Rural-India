"""DR classifier inference wrapper.

Uses a pretrained EfficientNetB0 model for 5-class DR severity grading.
"""

import os
os.environ["KERAS_BACKEND"] = "torch"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

try:
    import torch
    if hasattr(torch, "_dynamo"):
        torch._dynamo.config.suppress_errors = True
        torch._dynamo.config.disable = True
except Exception:
    pass

import numpy as np
import keras
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


HF_MODEL_ID = "Aldahmashi/DR-EfficientNetB0"
HF_REPO_FILE = "final_model.keras"

CLASS_NAMES = {
    0: "No DR",
    1: "Mild DR",
    2: "Moderate DR",
    3: "Severe DR",
    4: "Proliferative DR",
}

REFERABLE_THRESHOLD = 2


class DRClassifier:
    """Wrapper for DR severity classification."""

    def __init__(self):
        self.model = None
        self._loaded = False
        self._fallback = False
        self._load_error = ""

    def load_model(self) -> None:
        """Load the pretrained model."""
        if self._loaded and self.model is not None:
            return

        try:
            from huggingface_hub import hf_hub_download

            model_path = hf_hub_download(
                repo_id=HF_MODEL_ID,
                filename=HF_REPO_FILE,
            )
            self.model = keras.saving.load_model(model_path)
            self._loaded = True
            self._fallback = False
            print(f"Model loaded. Input: {self.model.input_shape}, Output: {self.model.output_shape}")
        except Exception as e:
            # Fallback demo mode so UI never dead-ends in competition/offline.
            self._load_error = str(e)
            self._fallback = True
            self._loaded = False
            print(f"WARNING: model load failed, using fallback demo mode: {e}")
            return

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """Predict DR severity from a preprocessed image.

        Falls back to a deterministic demo distribution when the
        HF model is unavailable, so the workflow stays demonstrable.
        """
        if self.model is None and not self._fallback:
            self.load_model()

        if self.model is None or self._fallback:
            # Demo fallback: neutral distribution, clearly flagged.
            probs = np.array([0.55, 0.20, 0.15, 0.06, 0.04], dtype=np.float32)
            return {
                "grade": 0,
                "label": CLASS_NAMES[0],
                "confidence": round(float(probs[0]), 4),
                "probabilities": {str(i): round(float(probs[i]), 4) for i in range(5)},
                "fallback": True,
                "note": f"Demo prediction (model unavailable: {self._load_error[:200]})" if self._load_error else "Demo prediction (model unavailable)",
            }

        raw_output = self.model.predict(image, verbose=0)
        probabilities = raw_output[0]

        probabilities = np.clip(probabilities, 0.0, None)
        total = probabilities.sum()
        if total > 0:
            probabilities = probabilities / total
        else:
            probabilities = np.ones(5) / 5.0

        predicted_class = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_class])

        return {
            "grade": predicted_class,
            "label": CLASS_NAMES[predicted_class],
            "confidence": round(confidence, 4),
            "probabilities": {
                str(i): round(float(probabilities[i]), 4)
                for i in range(5)
            },
        }

    def compute_referable_probability(self, probabilities: Dict[str, float]) -> float:
        """P(referable) = P(class 2) + P(class 3) + P(class 4)."""
        return round(
            probabilities.get("2", 0.0)
            + probabilities.get("3", 0.0)
            + probabilities.get("4", 0.0),
            4,
        )
