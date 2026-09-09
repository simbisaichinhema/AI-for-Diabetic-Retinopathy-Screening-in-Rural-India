#!/usr/bin/env python3
"""Test script for DR model integration."""

import os
os.environ["KERAS_BACKEND"] = "jax"

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import keras
from huggingface_hub import hf_hub_download
import cv2

CLASS_NAMES = {0: "No DR", 1: "Mild DR", 2: "Moderate DR", 3: "Severe DR", 4: "Proliferative DR"}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None)
    args = parser.parse_args()

    print("=" * 60)
    print("DR Screening Model Test")
    print("=" * 60)

    # 1. Load model
    print("\n[1] Loading model...", flush=True)
    model_path = hf_hub_download(
        repo_id="Aldahmashi/DR-EfficientNetB0",
        filename="final_model.keras",
    )
    model = keras.saving.load_model(model_path)
    print(f"    Input:  {model.input_shape}", flush=True)
    print(f"    Output: {model.output_shape}", flush=True)
    print(f"    Params: {model.count_params():,}", flush=True)

    # 2. Load test image
    print("\n[2] Loading test image...", flush=True)
    if args.image and Path(args.image).exists():
        img_path = args.image
    else:
        candidates = list(Path("data/aptos/train_images").glob("*.png"))
        if not candidates:
            print("    ERROR: No test image found", flush=True)
            sys.exit(1)
        img_path = str(candidates[0])

    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"    Path: {img_path}", flush=True)
    print(f"    Shape: {img.shape}", flush=True)

    # 3. Preprocess
    print("\n[3] Preprocessing...", flush=True)
    img_resized = cv2.resize(img, (224, 224))
    img_float = img_resized.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_norm = (img_float - mean) / std
    input_tensor = np.expand_dims(img_norm, axis=0)
    print(f"    Tensor: {input_tensor.shape} {input_tensor.dtype}", flush=True)

    # 4. Inference
    print("\n[4] Running inference...", flush=True)
    raw_output = model.predict(input_tensor, verbose=0)
    probs = raw_output[0]
    probs = np.clip(probs, 0.0, None)
    probs = probs / probs.sum()

    predicted = int(np.argmax(probs))
    confidence = float(probs[predicted])
    referable_prob = float(probs[2] + probs[3] + probs[4])

    print(f"\n    Predicted class: {predicted}", flush=True)
    print(f"    Predicted label: {CLASS_NAMES[predicted]}", flush=True)
    print(f"    Confidence:      {confidence*100:.1f}%", flush=True)
    print(f"    Referable:       {'YES' if predicted >= 2 else 'NO'}", flush=True)
    print(f"    Referable prob:  {referable_prob*100:.1f}%", flush=True)
    print(f"\n    Probabilities:", flush=True)
    for i in range(5):
        marker = " <--" if i == predicted else ""
        print(f"      Class {i} ({CLASS_NAMES[i]:20s}): {probs[i]*100:5.1f}%{marker}", flush=True)

    # 5. Validate
    print("\n[5] Validating...", flush=True)
    assert 0 <= predicted <= 4, f"Invalid class: {predicted}"
    assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"
    assert abs(probs.sum() - 1.0) < 0.01, f"Probs don't sum to 1: {probs.sum()}"
    for i in range(5):
        assert 0 <= probs[i] <= 1, f"Invalid prob for class {i}"
    print("    All checks PASSED", flush=True)

    # 6. Quality gate
    print("\n[6] Quality gate...", flush=True)
    from inference.quality_gate import QualityGate
    gate = QualityGate()
    quality = gate.assess(img)
    print(f"    Usable:   {quality['usable']}", flush=True)
    print(f"    Overall:  {quality['overall']:.3f}", flush=True)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
