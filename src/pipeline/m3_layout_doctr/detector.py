"""
M3 — DocTR Layout Detector (V3.1 corrected — object API).
Uses ocr_predictor object-based output: result.pages[0].blocks → lines → words.

Correct DocTR traversal (agents.md error_prevention_rules):
    ✓ DocumentFile.from_images([img_rgb])
    ✓ result.pages[0].blocks → block.lines → line.words → word.geometry
    ✓ word.geometry = ((x_min, y_min), (x_max, y_max)) — normalized [0.0, 1.0]
    ✓ Convert to pixels: x1 = int(x_min * img_w)
    ✗ Never call result["words"]  (dict API — do NOT use)
    ✗ Never assume dict-based output
    ✗ Never mix layout semantics into M3

Note: ocr_predictor performs both detection + recognition internally.
M3 uses ONLY the geometry output — text is discarded here (M4 handles OCR).

ARCHITECTURE CONTRACT (V3.1):
    ALL regions → type="text_block"
    NO semantic labels, NO column detection, NO reading order
    Confidence = model word.confidence
    region_id = "pending" → assigned by interface._process_page
"""
from __future__ import annotations

import cv2
import numpy as np

from src.data_model.layout import Region
from src.utils.bbox_utils import clip_bbox, is_valid

_CONFIDENCE_ACCEPT: float = 0.70
_CONFIDENCE_WARN:   float = 0.50

# Class-level model cache — loaded once per session, never reloaded per document
_MODEL_CACHE: dict[str, object] = {}


class DocTRLayoutDetector:
    """
    Wraps DocTR ocr_predictor for geometry-only text block extraction.
    Text output from recognition stage is intentionally discarded (M4 responsibility).
    """

    def __init__(self, arch: str = "db_resnet50"):
        self._arch = arch

    @property
    def model(self):
        """Lazy-load with class-level session cache (not reloaded per document)."""
        if self._arch not in _MODEL_CACHE:
            from doctr.models import ocr_predictor
            print(f"    [doctr]  Loading ocr_predictor('{self._arch}') — first call only...")
            _MODEL_CACHE[self._arch] = ocr_predictor(pretrained=True)
        return _MODEL_CACHE[self._arch]

    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = _CONFIDENCE_WARN,
    ) -> list[Region]:
        """
        Detect word-level bounding boxes using DocTR object API.

        Args:
            image:                uint8 ndarray (BGR or grayscale — converted to RGB).
            confidence_threshold: Minimum confidence to keep a detection.

        Returns:
            list[Region] — all type="text_block", region_id="pending".
        """
        # Input validation
        if image is None:
            raise ValueError("DocTRLayoutDetector.detect(): image is None")
        if not isinstance(image, np.ndarray):
            raise TypeError(
                f"Expected np.ndarray, got {type(image).__name__}. "
                "Ensure M2 returns ProcessedPage.clean_image as a numpy array."
            )

        # BGR → RGB (DocTR requires RGB uint8)
        img_rgb = _to_rgb(image)
        h, w = img_rgb.shape[:2]

        # Wrap for DocTR (DocumentFile.from_images accepts list of uint8 RGB arrays)
        from doctr.io import DocumentFile
        doc = DocumentFile.from_images([img_rgb])

        # Inference — object API
        result = self.model(doc)

        regions: list[Region] = []

        # Traverse: result.pages[0].blocks → block.lines → line.words
        page = result.pages[0]

        for block in page.blocks:
            for line in block.lines:
                for word in line.words:

                    # Geometry: ((x_min, y_min), (x_max, y_max)) normalized [0,1]
                    (x_min, y_min), (x_max, y_max) = word.geometry

                    # Convert relative → pixel coordinates
                    x1 = int(x_min * w)
                    y1 = int(y_min * h)
                    x2 = int(x_max * w)
                    y2 = int(y_max * h)

                    bbox = (x1, y1, x2, y2)

                    # Clip to image bounds and validate
                    bbox = clip_bbox(bbox, w, h)
                    if not is_valid(bbox):
                        continue

                    confidence = float(getattr(word, "confidence", 0.8))
                    if confidence < confidence_threshold:
                        continue

                    regions.append(Region(
                        region_id="pending",       # assigned by interface._process_page
                        type="text_block",         # HARD CONSTRAINT: no semantic label in M3
                        bbox=bbox,
                        confidence=confidence,
                        cropped_image=None,        # extracted by interface
                        flagged=confidence < _CONFIDENCE_ACCEPT,
                    ))

        # Debug hook (mandatory for first-run validation)
        print(f"    [DocTR DEBUG] page_detected_regions={len(regions)}")
        if len(regions) == 0:
            print("    [WARNING] No regions detected — check image quality or model output")

        return regions


# ── Image helper ───────────────────────────────────────────────────────────────

def _to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert BGR/gray/BGRA ndarray to RGB uint8 for DocTR."""
    if len(image.shape) == 2:
        img = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    else:
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return img.astype(np.uint8)
