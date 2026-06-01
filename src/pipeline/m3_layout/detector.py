"""
M3 — Layout Detector: classical CV contour-based text block detection.
V3 NEW — agents.md §MODULE_CONTRACTS → M3 Step 1

Algorithm (classical_cv backend — no ML required):
    1. Ensure grayscale binary image
    2. MORPH_CLOSE with horizontal kernel: connect characters into words/lines
    3. MORPH_CLOSE with vertical kernel:   connect lines into paragraph blocks
    4. findContours on the merged binary mask
    5. Filter contours by minimum area (0.08% of page)
    6. For each surviving contour: compute bounding rect + confidence estimate
    7. Return list of RawDetection objects

Confidence estimation (heuristic):
    Based on aspect ratio normality and fill ratio relative to bounding rect.
    Does NOT use any learned model — calibrated by visual inspection of real
    scanned document outputs.

BaseLayoutDetector:
    Abstract interface contract for all layout detection backends.
    Any alternative backend (LayoutLMv3, Detectron2) MUST implement detect().
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class RawDetection:
    """
    Intermediate detection result from any layout backend.
    Not yet filtered, ordered, or semantically typed.
    """
    bbox:       tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float                       # [0.0, 1.0]
    raw_type:   str = "unknown"             # backend-assigned type hint (may be overridden by semantic_grouper)


class BaseLayoutDetector(ABC):
    """Abstract contract for layout detection backends."""

    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5,
    ) -> list[RawDetection]:
        """
        Detect layout regions in a preprocessed document image.

        Args:
            image:                 uint8 ndarray (grayscale or BGR).
            confidence_threshold:  Discard detections below this value.
        Returns:
            List of RawDetection — unordered, unfiltered beyond the threshold.
        """
        ...


class ClassicalCVDetector(BaseLayoutDetector):
    """
    OpenCV morphological dilation + contour detection.
    V3 default backend — zero ML dependencies.
    """

    # Structuring element sizes (empirically tuned for 150-300 DPI scanned A4/letter)
    _H_KERNEL_W: int = 35   # horizontal dilation: connect chars into word-lines
    _H_KERNEL_H: int = 2    # keep thin to avoid merging adjacent text lines
    _V_KERNEL_W: int = 3    # vertical dilation: connect lines into paragraphs
    _V_KERNEL_H: int = 18   # vertical reach (approx 2–3 text line heights)

    # Minimum region area as fraction of page area
    _MIN_AREA_FRAC: float = 0.0008   # < 0.08% of page → noise

    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5,
    ) -> list[RawDetection]:
        """
        Detect text blocks via morphological grouping + contour extraction.

        Constraint: must_not_modify_image_pixels — all operations on copies.
        """
        binary = self._to_binary(image)
        merged = self._merge_components(binary)

        page_h, page_w = binary.shape[:2]
        min_area = page_h * page_w * self._MIN_AREA_FRAC

        contours, _ = cv2.findContours(
            merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detections: list[RawDetection] = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            box_area = cw * ch
            if box_area < min_area:
                continue

            fill_ratio = cv2.contourArea(contour) / max(box_area, 1)
            confidence = self._estimate_confidence(cw, ch, fill_ratio, page_w, page_h)

            if confidence < confidence_threshold:
                continue

            bbox = (x, y, x + cw, y + ch)
            detections.append(RawDetection(bbox=bbox, confidence=confidence))

        return detections

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _to_binary(image: np.ndarray) -> np.ndarray:
        """Convert to inverted binary (text=white, background=black) for morphology."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # If image is already binary (only 0 and 255 values), use as-is
        unique_vals = np.unique(gray)
        if len(unique_vals) <= 2:
            # Already binary — just ensure text is white
            if gray.mean() > 127:
                # White background: invert so text becomes white
                return cv2.bitwise_not(gray)
            return gray

        # Grayscale input: apply Otsu binarization
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def _merge_components(self, binary: np.ndarray) -> np.ndarray:
        """
        Morphological closing to group characters → words → lines → blocks.

        Two-pass approach:
        Pass 1 (horizontal): merges individual characters into text lines.
        Pass 2 (vertical):   merges adjacent lines into paragraph blocks.
        """
        h_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self._H_KERNEL_W, self._H_KERNEL_H)
        )
        v_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self._V_KERNEL_W, self._V_KERNEL_H)
        )
        h_merged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, h_kernel)
        v_merged = cv2.morphologyEx(h_merged, cv2.MORPH_CLOSE, v_kernel)
        return v_merged

    @staticmethod
    def _estimate_confidence(
        cw: int, ch: int, fill_ratio: float, page_w: int, page_h: int
    ) -> float:
        """
        Heuristic confidence score for a detected text block.

        Factors:
          - Aspect ratio: very thin/tall or very wide/flat regions are less certain
          - Fill ratio: how much of the bounding rect is actual contour area
          - Page-relative size: extremely large regions may be full-page artefacts
        """
        if ch < 6 or cw < 12:
            return 0.35

        aspect = cw / max(ch, 1)

        # Confidence starts from aspect normality
        if 1.5 <= aspect <= 25:
            base = 0.80
        elif 0.8 <= aspect < 1.5:
            base = 0.65    # roughly square — could be a figure or table cell
        elif 25 < aspect <= 50:
            base = 0.70    # very wide — header or separator line candidate
        else:
            base = 0.52    # unusual shape — borderline

        # Fill ratio adjustment (low fill = sparse text or complex graphic)
        fill_factor = max(0.70, min(1.0, fill_ratio * 1.5))
        confidence = base * fill_factor

        # Penalize extremely large blocks (> 60% of page area)
        page_frac = (cw * ch) / max(page_w * page_h, 1)
        if page_frac > 0.60:
            confidence *= 0.85

        return min(0.95, confidence)
