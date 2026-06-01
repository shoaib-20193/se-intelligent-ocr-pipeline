"""
M3 DocTR Layout Engine — interface (V3.1 corrected).

Entry point: layout_analysis(PreprocessedDocument, ProfileConfig) → LayoutDocument
Called by M7 orchestrator via src.pipeline.m3_layout.interface.layout_analysis().

Internal flow per page:
    1. Safety checks (None, type)
    2. DocTRLayoutDetector.detect(image) → list[Region(type="text_block")]
    3. Assign region_ids + extract crops
    4. Return LayoutPage(layout_type="raw_blocks", column_count=0)

V3.1 output contract:
    layout_type  = "raw_blocks"  ← signals: column structure NOT computed in M3
    column_count = 0             ← signals: not computed; M5 responsibility
    regions      = dense word-level text_blocks with pixel bboxes
"""
from __future__ import annotations

import numpy as np

from src.data_model.layout import LayoutPage, LayoutDocument
from src.data_model.preprocessed import PreprocessedDocument
from src.data_model.configs import ProfileConfig
from src.utils.bbox_utils import clip_bbox, is_valid

from src.pipeline.m3_layout_doctr.detector import DocTRLayoutDetector


class M3LayoutEngine:
    """
    DocTR-based M3 engine.
    Geometry extraction ONLY — no semantic interpretation.
    """

    def __init__(self, arch: str = "db_resnet50"):
        self.detector = DocTRLayoutDetector(arch=arch)

    # ── Primary M3 interface (called by M7 via m3_layout/interface.py) ────────

    def layout_analysis(
        self,
        document: PreprocessedDocument,
        profile: ProfileConfig,
    ) -> LayoutDocument:
        """M3 entry point: PreprocessedDocument → LayoutDocument."""
        confidence_threshold = getattr(profile, "confidence_threshold", 0.5)
        pages = []

        for page in document.pages:
            layout_page = self._process_page(
                image=page.clean_image,
                page_number=page.page_number,
                confidence_threshold=confidence_threshold,
            )
            pages.append(layout_page)

        return LayoutDocument(metadata=document.metadata, pages=pages)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _process_page(
        self,
        image,
        page_number: int,
        confidence_threshold: float,
    ) -> LayoutPage:
        """Run DocTR detection on a single page image."""

        # Safety: None guard
        if image is None:
            print(f"    [M3 WARN] page={page_number} — clean_image is None, returning empty page.")
            return LayoutPage(
                page_number=page_number, regions=[],
                layout_type="unknown", column_count=0,
            )

        # Safety: type guard
        if not isinstance(image, np.ndarray):
            raise TypeError(
                f"M3 expected np.ndarray for page {page_number}, "
                f"got {type(image).__name__}. "
                "Ensure M2 preprocess() returns ProcessedPage.clean_image as ndarray."
            )

        regions = self.detector.detect(image, confidence_threshold=confidence_threshold)

        # Assign region_ids + extract crops (non-destructive copy)
        for idx, region in enumerate(regions):
            region.region_id = f"p{page_number}-r{idx}"
            region.cropped_image = _extract_crop(image, region.bbox)

        return LayoutPage(
            page_number=page_number,
            regions=regions,
            layout_type="raw_blocks",    # V3.1: structural interpretation deferred to M5
            column_count=0,              # V3.1: not computed in M3
        )


# ── Crop helper ───────────────────────────────────────────────────────────────

def _extract_crop(image: np.ndarray, bbox: tuple) -> np.ndarray | None:
    """Extract region crop as a copy. Constraint: must_not_modify_image_pixels."""
    h, w = image.shape[:2]
    clipped = clip_bbox(bbox, w, h)
    if not is_valid(clipped):
        return None
    x1, y1, x2, y2 = clipped
    return image[y1:y2, x1:x2].copy()
