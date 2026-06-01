"""
M2 — Perspective corrector: detect document quad + apply warp.
agents.md §MODULE_CONTRACTS → M2 Step 7 (active if perspective_correction=True)
Fails safely if document contour confidence is weak.
"""
from __future__ import annotations
from typing import Optional

import cv2
import numpy as np
from src.utils.image_utils import to_grayscale

# Minimum area ratio of detected quad vs full image to be trusted
_MIN_AREA_RATIO: float = 0.20


def _order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order 4 points as [top-left, top-right, bottom-right, bottom-left].
    """
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left  (min x+y)
    rect[2] = pts[np.argmax(s)]   # bot-right (max x+y)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right (min y-x)
    rect[3] = pts[np.argmax(diff)]  # bot-left  (max y-x)
    return rect


def detect_document_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect the dominant 4-point document contour in the image.

    Returns:
        np.ndarray of shape (4, 2) with corner coordinates, or None if
        no reliable contour found.
    """
    gray = to_grayscale(image)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Sort by area descending; inspect the top candidates
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    image_area = image.shape[0] * image.shape[1]

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            area = cv2.contourArea(approx)
            if area / image_area >= _MIN_AREA_RATIO:
                return approx.reshape(4, 2).astype(np.float32)

    return None  # No reliable quad found


def apply_perspective_warp(
    image: np.ndarray, contour: np.ndarray
) -> np.ndarray:
    """
    Apply a four-point perspective warp to produce a top-down view.

    Args:
        image:   Source image.
        contour: (4, 2) float32 array of corner coordinates.
    Returns:
        Warped image (uint8).
    """
    rect = _order_points(contour)
    tl, tr, br, bl = rect

    # Compute output dimensions
    w_top = float(np.linalg.norm(tr - tl))
    w_bot = float(np.linalg.norm(br - bl))
    h_left = float(np.linalg.norm(bl - tl))
    h_right = float(np.linalg.norm(br - tr))

    out_w = max(1, int(max(w_top, w_bot)))
    out_h = max(1, int(max(h_left, h_right)))

    dst = np.array(
        [[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (out_w, out_h))


def correct_perspective(image: np.ndarray) -> tuple[np.ndarray, bool]:
    """
    Top-level perspective correction call.

    Returns:
        (result_image, success)
        If no reliable contour found → returns (original_image, False).
    """
    contour = detect_document_contour(image)
    if contour is None:
        return image, False
    warped = apply_perspective_warp(image, contour)
    return warped, True
