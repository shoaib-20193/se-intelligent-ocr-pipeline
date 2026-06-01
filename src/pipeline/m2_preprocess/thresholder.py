"""
M2 — Thresholder: Otsu and adaptive binarisation.
V2.4 upgrade: exposed adaptive_block_size and adaptive_C as configurable params.
agents.md §MODULE_CONTRACTS → M2 Step 5 (active if thresholding=True)

V2.4 changes vs V2.0:
- adaptive_block_size and adaptive_C now passed in from ProfileConfig
- Smaller block_size (15–21) and higher C (15–20) recommended for blurry documents
- Reduces character welding caused by V2.0 fixed parameters (block=31, C=10)
"""
from __future__ import annotations
import cv2
import numpy as np
from src.utils.image_utils import to_grayscale

MODE_OTSU     = "otsu"
MODE_ADAPTIVE = "adaptive"


def apply_otsu(image: np.ndarray) -> np.ndarray:
    """
    Apply Otsu global thresholding.
    Best for: clean, uniformly-lit scans with clear bimodal grayscale histogram.
    Returns single-channel binary image (255 = foreground, 0 = background).
    """
    gray = to_grayscale(image)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def apply_adaptive(
    image: np.ndarray,
    block_size: int = 31,
    c_constant: int = 10,
) -> np.ndarray:
    """
    Apply Gaussian adaptive thresholding.
    Best for: uneven illumination, blurry documents, mobile captures.

    V2.4: block_size and c_constant are now caller-supplied from ProfileConfig.
    - Smaller block_size (15–21) → finer local windows → less over-merging on blurry text
    - Higher c_constant (15–20) → more aggressive separation → thinner, less-welded strokes

    Character welding guide:
        If 'rn' reads as 'm': increase C (+5) and decrease block_size (−4)
        If 'cl' reads as 'd': increase C (+5)
        If letter counters fill (e.g. 'o', 'a'): decrease C (−3) or increase block_size (+4)

    Args:
        image:       Input ndarray (grayscale or BGR).
        block_size:  Neighbourhood size (must be odd, ≥ 3). Default 31.
        c_constant:  Subtracted from weighted mean. Default 10. Range: 5–25.
    Returns:
        Binary uint8 ndarray.
    """
    # Enforce odd block_size ≥ 3
    bs = max(3, block_size)
    if bs % 2 == 0:
        bs += 1

    gray = to_grayscale(image)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        bs,
        c_constant,
    )


def threshold(
    image: np.ndarray,
    mode: str = MODE_OTSU,
    block_size: int = 31,
    c_constant: int = 10,
) -> np.ndarray:
    """
    Unified thresholding entry point.

    Args:
        image:       Input ndarray.
        mode:        "otsu" (default) | "adaptive"
        block_size:  Used only when mode="adaptive". Default 31.
        c_constant:  Used only when mode="adaptive". Default 10.
    Returns:
        Binary uint8 ndarray.
    Raises:
        ValueError if mode is unrecognised.
    """
    if mode == MODE_OTSU:
        return apply_otsu(image)
    elif mode == MODE_ADAPTIVE:
        return apply_adaptive(image, block_size=block_size, c_constant=c_constant)
    else:
        raise ValueError(f"Unknown threshold mode '{mode}'. Use 'otsu' or 'adaptive'.")
