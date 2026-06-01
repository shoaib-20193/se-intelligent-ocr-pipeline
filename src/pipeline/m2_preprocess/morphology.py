"""
M2 — Morphological operations: character isolation after thresholding.
V2.4 NEW module — agents.md §MODULE_CONTRACTS → M2 V2.4

Pipeline position: AFTER thresholding (binary image input required)

Rationale:
    After adaptive thresholding, blurry text produces binary blobs where
    adjacent characters remain connected by thin bridges of ink.
    Morphological opening (erode → dilate) breaks these micro-bridges
    while preserving the core character strokes — if kernel is conservative.

    Critical constraint: kernel_size must stay ≤ 2 for typical document fonts.
    Larger kernels destroy thin strokes (e.g. 'i', 'l', '1', punctuation).

    Priority:
        opening  → character SEPARATION (remove bridges)
        closing  → stroke REPAIR (fill gaps in broken strokes)
        In most cases, only opening is needed.
"""
from __future__ import annotations
import cv2
import numpy as np


def morphology_open(image: np.ndarray, kernel_size: int = 2) -> np.ndarray:
    """
    Apply morphological opening to separate adjacent characters.

    Morphological opening = erosion followed by dilation with same kernel.
    Removes thin pixel bridges between characters without shrinking their bodies
    significantly, provided kernel_size stays conservative (1–2).

    Args:
        image:       Binary uint8 ndarray (255 = foreground text, 0 = background).
                     Input must already be thresholded.
        kernel_size: Square structuring element size (default 2).
                     1 = minimal, removes 1-px bridges only.
                     2 = removes 2-px bridges (recommended for blurry text).
                     3+ = risk of destroying thin strokes — use with caution.
    Returns:
        Binary uint8 ndarray with micro-bridges removed.
    """
    k = max(1, kernel_size)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)


def morphology_close(image: np.ndarray, kernel_size: int = 2) -> np.ndarray:
    """
    Apply morphological closing to repair broken character strokes.

    Morphological closing = dilation followed by erosion with same kernel.
    Fills small intra-character gaps caused by uneven illumination or
    aggressive thresholding.

    Args:
        image:       Binary uint8 ndarray (thresholded).
        kernel_size: Square structuring element size (default 2).
    Returns:
        Binary uint8 ndarray with small stroke gaps filled.
    """
    k = max(1, kernel_size)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)


def apply_morphology(
    image: np.ndarray,
    opening: bool = False,
    closing: bool = False,
    kernel_size: int = 2,
) -> tuple[np.ndarray, list[str]]:
    """
    Unified morphology entry point. Applies opening then closing in that order.

    Args:
        image:       Thresholded binary uint8 ndarray.
        opening:     Apply morphological opening (character separation).
        closing:     Apply morphological closing (stroke gap repair).
        kernel_size: Kernel size for both operations.
    Returns:
        (processed_image, ops_applied_list)
    """
    img = image.copy()
    ops: list[str] = []

    if opening:
        img = morphology_open(img, kernel_size=kernel_size)
        ops.append(f"morph_open(k={kernel_size})")

    if closing:
        img = morphology_close(img, kernel_size=kernel_size)
        ops.append(f"morph_close(k={kernel_size})")

    return img, ops
