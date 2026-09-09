"""Lesion evidence analysis for DR screening.

Provides visual evidence of detected lesions:
- Microaneurysms
- Hemorrhages
- Hard exudates
- Soft exudates

The system should clearly distinguish:
MODEL PREDICTION from SUPPORTING VISUAL EVIDENCE.
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple


# Lesion colors for visualization
LESION_COLORS = {
    "microaneurysms": (255, 0, 0),     # Red
    "hemorrhages": (0, 0, 255),        # Blue
    "hard_exudates": (255, 255, 0),    # Yellow
    "soft_exudates": (0, 255, 255),    # Cyan
}


def analyze_lesions(
    image: np.ndarray,
    lesion_masks: Optional[Dict[str, np.ndarray]] = None,
    model_predictions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Analyze lesion evidence in a fundus image.

    This function provides visual evidence from lesion detection models.
    It does NOT make clinical diagnoses.

    Args:
        image: Fundus image (H, W, 3).
        lesion_masks: Dictionary of lesion type -> binary mask.
        model_predictions: Model confidence for each lesion type.

    Returns:
        Dictionary with lesion analysis results.
    """
    results = {
        "lesions_detected": {},
        "total_lesion_area": 0,
        "lesion_regions": [],
        "evidence_available": False,
    }

    if lesion_masks is None and model_predictions is None:
        return results

    # Process each lesion type
    for lesion_type in ["microaneurysms", "hemorrhages", "hard_exudates", "soft_exudates"]:
        lesion_info = {
            "detected": False,
            "confidence": 0.0,
            "area_pixels": 0,
            "area_ratio": 0.0,
            "num_components": 0,
            "bounding_boxes": [],
        }

        # If we have a mask, compute metrics
        if lesion_masks and lesion_type in lesion_masks:
            mask = lesion_masks[lesion_type]
            if mask.max() > 0:
                lesion_info["detected"] = True
                lesion_info["area_pixels"] = int(np.sum(mask > 0))
                lesion_info["area_ratio"] = float(np.mean(mask > 0))

                # Find connected components
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                    mask.astype(np.uint8)
                )
                lesion_info["num_components"] = num_labels - 1  # Exclude background

                # Get bounding boxes
                for i in range(1, num_labels):
                    x, y, w, h, area = stats[i]
                    lesion_info["bounding_boxes"].append({
                        "x": int(x), "y": int(y),
                        "width": int(w), "height": int(h),
                        "area": int(area),
                    })

        # If we have model predictions, use them
        if model_predictions and lesion_type in model_predictions:
            lesion_info["confidence"] = float(model_predictions[lesion_type])
            if lesion_info["confidence"] > 0.5:
                lesion_info["detected"] = True

        results["lesions_detected"][lesion_type] = lesion_info
        results["total_lesion_area"] += lesion_info["area_pixels"]

        if lesion_info["detected"]:
            results["evidence_available"] = True
            results["lesion_regions"].append(lesion_type)

    return results


def generate_lesion_overlay(
    original_image: np.ndarray,
    lesion_masks: Dict[str, np.ndarray],
    alpha: float = 0.5,
) -> np.ndarray:
    """Generate overlay visualization of detected lesions.

    Args:
        original_image: Original fundus image (H, W, 3).
        lesion_masks: Dictionary of lesion type -> binary mask.
        alpha: Overlay transparency.

    Returns:
        Overlay image with colored lesion regions.
    """
    if original_image.dtype != np.uint8:
        if original_image.max() <= 1.0:
            overlay = (original_image * 255).astype(np.uint8)
        else:
            overlay = original_image.astype(np.uint8)
    else:
        overlay = original_image.copy()

    # Create colored overlay
    colored_overlay = np.zeros_like(overlay)

    for lesion_type, mask in lesion_masks.items():
        if mask.max() > 0 and lesion_type in LESION_COLORS:
            color = LESION_COLORS[lesion_type]
            colored_overlay[mask > 0] = color

    # Blend
    result = cv2.addWeighted(overlay, 1 - alpha, colored_overlay, alpha, 0)

    return result


def generate_lesion_evidence_report(
    analysis: Dict[str, Any],
) -> str:
    """Generate human-readable lesion evidence report.

    Args:
        analysis: Output from analyze_lesions.

    Returns:
        Formatted text report.
    """
    lines = ["=== Lesion Evidence Report ===\n"]

    if not analysis["evidence_available"]:
        lines.append("No lesion evidence detected.\n")
        return "\n".join(lines)

    for lesion_type, info in analysis["lesions_detected"].items():
        if info["detected"]:
            status = "DETECTED" if info["confidence"] > 0.5 else "Possible"
            lines.append(f"• {lesion_type.replace('_', ' ').title()}: {status}")
            if info["area_pixels"] > 0:
                lines.append(f"  Area: {info['area_pixels']} pixels ({info['area_ratio']:.2%})")
            if info["num_components"] > 0:
                lines.append(f"  Count: {info['num_components']} region(s)")
            if info["confidence"] > 0:
                lines.append(f"  Confidence: {info['confidence']:.1%}")
            lines.append("")

    lines.append("NOTE: This is visual evidence from the AI model, not a clinical diagnosis.")
    lines.append("Clinical review by an ophthalmologist is required.")

    return "\n".join(lines)
