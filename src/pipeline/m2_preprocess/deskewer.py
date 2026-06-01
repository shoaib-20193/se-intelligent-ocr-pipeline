"""
M2 — Deskewer: skew angle detection + correction.
agents.md §MODULE_CONTRACTS → M2 Step 3
Target: correct skew to within ±1° (agents.md §MODULE_CONTRACTS → M2)
"""
from __future__ import annotations
import cv2
import numpy as np
from src.utils.image_utils import to_grayscale

# Angles within this range are considered negligible (skip warp)
_SKIP_THRESHOLD_DEG: float = 0.5


def detect_skew_angle(image: np.ndarray) -> float:
    """
    Detect document skew angle using the projection-profile method.

    Approach:
    1. Binarise image (Otsu) → white text on black background.
    2. For each candidate angle in [-15°, +15°], compute horizontal projection profile.
    3. Select angle whose profile has maximum variance (sharpest row peaks = aligned text).

    Returns:
        Detected skew angle in degrees. Positive = clockwise tilt.
    """
    gray = to_grayscale(image)

    # Binarise: invert so text is white
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    h, w = binary.shape
    best_angle = 0.0
    best_score = -1.0

    for angle in np.arange(-15, 15.5, 0.5):
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rotated = cv2.warpAffine(
            binary, M, (w, h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        # Sum each row → projection profile
        profile = np.sum(rotated, axis=1).astype(np.float64)
        score = float(np.var(profile))
        if score > best_score:
            best_score = score
            best_angle = float(angle)

    return best_angle


def deskew(image: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Detect and correct document skew.

    Args:
        image: Input uint8 ndarray (grayscale or BGR).
    Returns:
        (corrected_image, detected_angle_degrees)
        corrected_image has same dtype and shape as input.
    """
    angle = detect_skew_angle(image)

    if abs(angle) < _SKIP_THRESHOLD_DEG:
        return image, angle

    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)

    # Fill border with white (255) to avoid black padding artifacts on documents
    border_val = 255 if image.ndim == 2 else (255, 255, 255)
    corrected = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_val,
    )
    return corrected, angle
