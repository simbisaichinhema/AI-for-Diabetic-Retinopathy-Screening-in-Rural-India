"""Tests for DR classifier (matches inference/classifier.py API)."""

import pytest

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

    def test_predict_without_model_fails_closed(self, monkeypatch):
        """Without the HF model, prediction must fail rather than synthesize results."""
        classifier = DRClassifier()
        classifier.model = None
        classifier._load_error = "unit-test"
        def fail_load():
            raise RuntimeError("unit-test")
        monkeypatch.setattr(classifier, "load_model", fail_load)
        with pytest.raises(RuntimeError, match="unit-test"):
            classifier.predict(None)
