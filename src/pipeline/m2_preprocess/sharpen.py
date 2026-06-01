"""
M2 — Unsharp Masking: edge restoration before CLAHE + thresholding.
V2.4 NEW module — agents.md §MODULE_CONTRACTS → M2 V2.4

Pipeline position: AFTER deskew, BEFORE CLAHE (agents.md §MODULE_CONTRACTS → M2 V2.4)

Rationale:
    Blurry documents lose high-frequency edge information needed for character separation.
    Applying sharpening BEFORE thresholding restores gradient magnitude at character
    boundaries, producing thinner, better-separated binary strokes.

    Unsharp masking formula:
        sharp = (1 + strength) * original − strength * blurred
        equivalent: cv2.addWeighted(img, 1+s, blur, -s, 0)

    OCR note: Keep strength ≤ 0.6 to avoid halo amplification that can
    artificially widen strokes and undo the separation benefit.
"""
from __future__ import annotations
import cv2
import numpy as np


def unsharp_mask(
    image: np.ndarray,
    strength: float = 0.5,
    blur_kernel: int = 5,
) -> np.ndarray:
    """
    Apply unsharp masking for edge restoration.

    Args:
        image:       Input uint8 ndarray (grayscale or BGR).
        strength:    Sharpening alpha (default 0.5). Range: 0.1 – 0.8.
                     Higher = sharper but more halo risk.
        blur_kernel: Gaussian kernel size for blurred reference (default 5).
    Returns:
        Edge-enhanced uint8 ndarray, same shape and channels as input.
    """
    # Enforce odd kernel
    k = max(3, blur_kernel)
    if k % 2 == 0:
        k += 1

    blurred = cv2.GaussianBlur(image, (k, k), sigmaX=0)

    # addWeighted: result = alpha * src1 + beta * src2 + gamma
    # alpha = 1.0 + strength (amplify original)
    # beta  = -strength      (subtract blurred = add high-freq)
    sharpened = cv2.addWeighted(
        image, 1.0 + strength,
        blurred, -strength,
        0,   # gamma (offset)
    )
    return sharpened


def sharpen(image: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """
    OCR-safe sharpening entry point.

    Applies unsharp masking with blur_kernel=5 (matches typical character
    stroke width for document-scale text).

    Args:
        image:    Input uint8 ndarray.
        strength: Sharpening intensity (default 0.5). Keep ≤ 0.6 for OCR.
    Returns:
        Sharpened uint8 ndarray.
    """
    return unsharp_mask(image, strength=strength, blur_kernel=5)
