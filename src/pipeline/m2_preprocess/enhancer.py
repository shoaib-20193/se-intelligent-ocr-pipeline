"""
M2 — CLAHE Enhancer: contrast-limited adaptive histogram equalization. V2.3 upgrade.
agents.md §MODULE_CONTRACTS → M2 Step 4 (ALWAYS ACTIVE — no profile flag)

V2.3 changes vs V2.0:
- clip_limit now configurable via ProfileConfig.clahe_clip_limit
- Default reduced from 2.0 → 1.5 (conservative, avoids stroke thickening)
- Documented why subtle enhancement is preferred for OCR text separation
"""
from __future__ import annotations
import cv2
import numpy as np
from src.utils.image_utils import is_grayscale


def enhance_clahe(
    image: np.ndarray,
    clip_limit: float = 1.5,
    tile_grid: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

    CLAHE is ALWAYS executed regardless of profile flags (agents.md §MODULE_CONTRACTS → M2).

    OCR note: Conservative clip_limit (1.5) is preferred over aggressive (3.0+).
    High clip_limit amplifies blur halos and thickens character strokes,
    which causes adjacent characters to merge during thresholding.

    Args:
        image:      Input uint8 ndarray (grayscale or BGR).
        clip_limit: Contrast amplification cap (default 1.5 — OCR-conservative).
                    Profile 'high_accuracy' uses 2.0; 'blurred_document' uses 1.0.
        tile_grid:  Grid size for local histogram computation (default (8,8)).
    Returns:
        Contrast-enhanced uint8 ndarray, same shape and channels as input.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)

    if is_grayscale(image):
        return clahe.apply(image)

    # For BGR: apply CLAHE only to the L (luminance) channel in LAB colour space
    # This prevents colour distortion while enhancing perceived contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    l_eq = clahe.apply(l_ch)
    lab_eq = cv2.merge([l_eq, a_ch, b_ch])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
