"""Tests for preprocessing modules."""

import pytest
import numpy as np
import cv2

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.retinal_crop import crop_retinal, detect_retinal_mask
from preprocessing.illumination import normalize_illumination
from preprocessing.clahe import apply_clahe
from preprocessing.transforms import preprocess_for_model


class TestRetinalCrop:
    def test_detect_retinal_mask(self):
        # Create a synthetic fundus image with circular region
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        cv2.circle(img, (112, 112), 80, (200, 100, 50), -1)

        mask = detect_retinal_mask(img)
        assert mask.shape == (224, 224)
        assert mask.max() == 1
        assert mask.min() == 0

    def test_crop_retinal(self):
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        cv2.circle(img, (112, 112), 80, (200, 100, 50), -1)

        cropped = crop_retinal(img, mask_retina=True)
        assert cropped.shape[0] <= 224
        assert cropped.shape[1] <= 224


class TestIllumination:
    def test_normalize_illumination(self):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = normalize_illumination(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_normalize_grayscale(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = normalize_illumination(img)

        assert result.shape == img.shape


class TestCLAHE:
    def test_apply_clahe_color(self):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_apply_clahe_grayscale(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == img.shape


class TestPreprocessForModel:
    def test_preprocess_imagenet(self):
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = preprocess_for_model(img, normalization="imagenet")

        assert result.shape == (224, 224, 3)
        assert result.dtype == np.float32

    def test_preprocess_minmax(self):
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = preprocess_for_model(img, normalization="minmax")

        assert result.shape == (224, 224, 3)
        assert result.min() >= 0
        assert result.max() <= 1
