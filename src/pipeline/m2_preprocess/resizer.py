"""
M2 — Resizer: scale image by resize_scale from ProfileConfig.
agents.md §MODULE_CONTRACTS → M2 Step 6
"""
from __future__ import annotations
import cv2
import numpy as np


def resize(image: np.ndarray, scale: float) -> np.ndarray:
    """
    Resize image by a uniform scale factor, preserving aspect ratio.

    - scale = 1.0 → no change (returns original reference)
    - scale > 1.0 → upscale (CUBIC interpolation for quality)
    - scale < 1.0 → downscale (AREA interpolation to avoid aliasing)
    - scale ≤ 0  → raises ValueError

    Args:
        image: Input uint8 ndarray (any channel count).
        scale: Positive float scale factor.
    Returns:
        Resized uint8 ndarray.
    """
    if scale <= 0:
        raise ValueError(f"resize_scale must be > 0, got {scale}")

    if abs(scale - 1.0) < 1e-6:
        return image   # no-op: skip unnecessary copy

    h, w = image.shape[:2]
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    interp = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
    return cv2.resize(image, (new_w, new_h), interpolation=interp)
