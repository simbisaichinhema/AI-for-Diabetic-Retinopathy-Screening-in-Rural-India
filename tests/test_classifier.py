"""Tests for DR classifier (matches inference/classifier.py API)."""

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.classifier import DRClassifier, CLASS_NAMES, REFERABLE_THRESHOLD


class TestDRClassifier:
    def test_class_names(self):
        assert CLASS_NAMES[0] == "No DR"
        assert CLASS_NAMES[1] == "Mild DR"
        assert CLASS_NAMES[2] == "Moderate DR"
        assert CLASS_NAMES[3] == "Severe DR"
        assert CLASS_NAMES[4] == "Proliferative DR"
        assert REFERABLE_THRESHOLD == 2

    def test_classifier_init(self):
        classifier = DRClassifier()
        assert classifier.model is None
        assert classifier._loaded is False

    def test_compute_referable(self):
        classifier = DRClassifier()
        probs = {"0": 0.5, "1": 0.2, "2": 0.15, "3": 0.1, "4": 0.05}
        assert classifier.compute_referable_probability(probs) == 0.3

    def test_predict_fallback_without_model(self):
        """Without HF model, predict() must return flagged demo output, not crash."""
        classifier = DRClassifier()
        classifier._fallback = True
        classifier._load_error = "unit-test"
        out = classifier.predict(np.zeros((1, 224, 224, 3), dtype=np.float32))
        assert out["grade"] == 0
        assert out["label"] == "No DR"
        assert out["fallback"] is True
        assert abs(sum(out["probabilities"].values()) - 1.0) < 0.01
