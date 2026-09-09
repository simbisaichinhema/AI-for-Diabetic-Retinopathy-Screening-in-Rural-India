"""Tests for image quality assessment."""

import pytest
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.image_quality import (
    assess_image_quality,
    compute_focus_score,
    compute_illumination_score,
    compute_fov_score,
)


class TestFocusScore:
    def test_sharp_image(self):
        # Create a sharp image with clear edges
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[100:124, 100:124] = 255

        score = compute_focus_score(img)
        assert 0 <= score <= 1

    def test_blurry_image(self):
        # Create a blurry image
        img = np.ones((224, 224, 3), dtype=np.uint8) * 128
        score = compute_focus_score(img)
        assert 0 <= score <= 1


class TestIlluminationScore:
    def test_good_illumination(self):
        img = np.ones((224, 224, 3), dtype=np.uint8) * 128
        score = compute_illumination_score(img)
        assert 0 <= score <= 1

    def test_dark_image(self):
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        score = compute_illumination_score(img)
        assert 0 <= score <= 1


class TestFOVScore:
    def test_good_fov(self):
        # Create image with good retinal coverage
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[50:174, 50:174] = 200

        score = compute_fov_score(img)
        assert 0 <= score <= 1

    def test_poor_fov(self):
        # Create image with small retinal region
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[100:124, 100:124] = 200

        score = compute_fov_score(img)
        assert 0 <= score <= 1


class TestQualityAssessment:
    def test_good_image(self):
        # Create a reasonable quality image
        img = np.random.randint(50, 200, (224, 224, 3), dtype=np.uint8)
        result = assess_image_quality(img)

        assert hasattr(result, 'usable')
        assert hasattr(result, 'focus_score')
        assert hasattr(result, 'illumination_score')
        assert hasattr(result, 'fov_score')
        assert hasattr(result, 'overall_score')

    def test_result_dict(self):
        img = np.random.randint(50, 200, (224, 224, 3), dtype=np.uint8)
        result = assess_image_quality(img)
        d = result.to_dict()

        assert 'usable' in d
        assert 'focus_score' in d
