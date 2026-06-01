"""
image_utils — Shared image helpers for all pipeline stages.
See agents.md §TECH_STACK → OpenCV (CON-3)
"""
from __future__ import annotations
import os
from typing import Optional

import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR or BGRA image to single-channel grayscale. No-op if already gray."""
    if image.ndim == 2:
        return image
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def to_bgr(image: np.ndarray) -> np.ndarray:
    """Convert grayscale to 3-channel BGR. No-op if already BGR/BGRA."""
    if image.ndim == 3:
        return image
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


def is_grayscale(image: np.ndarray) -> bool:
    return image.ndim == 2


def get_dimensions(image: np.ndarray) -> tuple[int, int]:
    """Return (width, height)."""
    h, w = image.shape[:2]
    return w, h


def safe_load(path: str, flag: int = cv2.IMREAD_COLOR) -> Optional[np.ndarray]:
    """
    Load an image from disk; return None on failure (never raises).
    Uses IMREAD_COLOR by default → always returns BGR ndarray.
    """
    if not os.path.isfile(path):
        return None
    img = cv2.imread(path, flag)
    return img if img is not None else None


def normalize_uint8(image: np.ndarray) -> np.ndarray:
    """Ensure image is uint8 [0, 255]. Clips and converts if needed."""
    if image.dtype == np.uint8:
        return image
    img = np.clip(image, 0, 255)
    return img.astype(np.uint8)


def save_debug_image(image: np.ndarray, path: str) -> bool:
    """
    Write image to disk for visual inspection. Creates parent dirs.
    Returns True on success, False on failure.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return cv2.imwrite(path, image)
    except Exception:
        return False


def side_by_side(left: np.ndarray, right: np.ndarray, gap: int = 20) -> np.ndarray:
    """
    Create a horizontally joined comparison image (left | gap | right).
    Both images are converted to BGR before joining.
    """
    left_bgr = to_bgr(left)
    right_bgr = to_bgr(right)

    h = max(left_bgr.shape[0], right_bgr.shape[0])

    def pad_height(img: np.ndarray, target_h: int) -> np.ndarray:
        dh = target_h - img.shape[0]
        if dh <= 0:
            return img
        pad = np.full((dh, img.shape[1], 3), 255, dtype=np.uint8)
        return np.vstack([img, pad])

    left_bgr = pad_height(left_bgr, h)
    right_bgr = pad_height(right_bgr, h)
    divider = np.full((h, gap, 3), 200, dtype=np.uint8)
    return np.hstack([left_bgr, divider, right_bgr])
