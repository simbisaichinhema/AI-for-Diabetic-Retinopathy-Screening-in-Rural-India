"""Integration tests for DR screening pipeline."""

import pytest
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.pipeline import DRScreeningPipeline
from inference.quality_gate import QualityGate
from inference.report_generator import ClinicalReportGenerator


class TestQualityGate:
    def test_assessment(self):
        gate = QualityGate()
        img = np.random.randint(50, 200, (224, 224, 3), dtype=np.uint8)
        result = gate.assess(img)

        assert 'usable' in result
        assert 'focus' in result
        assert 'illumination' in result
        assert 'field_of_view' in result
        assert 'action' in result


class TestReportGenerator:
    def test_generate_report(self):
        gen = ClinicalReportGenerator()

        quality = {"usable": True, "focus": 0.9, "illumination": 0.85, "field_of_view": 0.92, "overall": 0.89}
        prediction = {"grade": 2, "label": "Moderate DR", "confidence": 0.82, "probabilities": {}}
        report = gen.generate(
            case_id="TEST-001",
            quality=quality,
            prediction=prediction,
            referable=True,
        )

        assert report['case_id'] == "TEST-001"
        assert report['referable_dr']['is_referable'] is True
        assert 'RECOMMENDATION' in report['recommendation'] or 'Refer' in report['recommendation']

    def test_format_text(self):
        gen = ClinicalReportGenerator()
        quality = {"usable": True, "focus": 0.9, "illumination": 0.85, "field_of_view": 0.92, "overall": 0.89}
        prediction = {"grade": 0, "label": "No DR", "confidence": 0.95, "probabilities": {}}

        report = gen.generate(
            case_id="TEST-002",
            quality=quality,
            prediction=prediction,
            referable=False,
        )

        text = gen.format_text_report(report)
        assert "TEST-002" in text
        assert "No DR" in text


class TestPipelineIntegration:
    def test_pipeline_init(self):
        pipeline = DRScreeningPipeline()
        assert pipeline.quality_gate is not None
        assert pipeline.classifier is not None

    def test_screen_with_bad_quality(self):
        pipeline = DRScreeningPipeline()
        # Create very dark image (should fail quality)
        img = np.zeros((224, 224, 3), dtype=np.uint8)

        result = pipeline.screen(img)

        # Either recapture or completed with low quality
        assert 'case_id' in result
        assert 'status' in result
