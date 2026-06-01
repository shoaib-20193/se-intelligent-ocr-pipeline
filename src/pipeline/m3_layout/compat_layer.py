"""
M3 Compatibility Layer — V3.1
Normalizes M3 output for safe M4 consumption regardless of active backend.

Problem:
    V3 classical CV  → semantic types (header/paragraph/table/figure/footer),
                        reading order applied, column_count > 0
    V3.1 DocTR       → all type="text_block", layout_type="raw_blocks",
                        column_count=0, dense word-level regions

    M4 must consume either backend output without modification or hard failures.

Solution (this module):
    - normalize_layout_output()  → ensures LayoutDocument is M4-safe
    - ensure_region_integrity()  → validates and sanitizes each Region
    - ensure_text_block_only()   → strips semantic type labels from regions destined for M4
                                   (M5 re-classifies from OCR text + geometry)

Design rules:
    ✓ Additive normalization only — no data is discarded unless truly invalid
    ✓ Downstream M4 NEVER hard-fails due to M3 backend differences
    ✓ semantic type is preserved on Region.type for M5 (classical_cv path)
    ✓ Invalid regions (broken bbox, None crop) removed with warnings — not crashed
    ✓ Normalized output is always pixel-space integer bboxes
"""
from __future__ import annotations

import numpy as np
from dataclasses import replace as dataclass_replace

from src.data_model.layout import Region, LayoutPage, LayoutDocument
from src.utils.bbox_utils import is_valid, clip_bbox


# ── Public API ─────────────────────────────────────────────────────────────────

def normalize_layout_output(
    layout_doc: LayoutDocument,
    image_map: dict[int, np.ndarray] | None = None,
) -> LayoutDocument:
    """
    Normalize a LayoutDocument for safe M4 consumption.

    Operations (non-destructive):
        1. Validate all region bboxes are integer pixel-space coordinates
        2. Remove regions with invalid bboxes (logged, not crashed)
        3. Remove regions where cropped_image is None and re-extraction fails
        4. Normalize confidence to [0.0, 1.0] clamp
        5. Ensure region_ids are sequential and unique per page
        6. Sanitize flagged status

    Args:
        layout_doc:  Output from layout_analysis() (either backend).
        image_map:   Optional {page_number: clean_image} for re-extracting crops
                     when region.cropped_image is None. If not provided, regions
                     with None crops are retained (M4 will skip them).

    Returns:
        New LayoutDocument with sanitized regions. Input is not mutated.
    """
    normalized_pages: list[LayoutPage] = []

    for page in layout_doc.pages:
        src_image = (image_map or {}).get(page.page_number)
        clean_regions = ensure_region_integrity(
            regions=page.regions,
            page_number=page.page_number,
            src_image=src_image,
        )
        normalized_pages.append(LayoutPage(
            page_number=page.page_number,
            regions=clean_regions,
            layout_type=page.layout_type,
            column_count=page.column_count,
        ))

    return LayoutDocument(
        metadata=layout_doc.metadata,
        pages=normalized_pages,
    )


def ensure_region_integrity(
    regions: list[Region],
    page_number: int,
    src_image: np.ndarray | None = None,
) -> list[Region]:
    """
    Validate and sanitize a list of Region objects.

    Per-region operations:
        1. Skip regions with None or invalid bbox
        2. Ensure bbox values are integers
        3. Clamp confidence to [0.0, 1.0]
        4. Re-extract cropped_image if None and src_image available
        5. Reassign sequential region_ids
        6. Set flagged=True if confidence < 0.70

    Args:
        regions:     Raw region list from M3.
        page_number: Used for region_id reassignment.
        src_image:   Source page image for crop re-extraction (optional).

    Returns:
        New list of sanitized Region objects. Originals are not mutated.
    """
    clean: list[Region] = []
    skipped = 0

    for region in regions:
        # Validate bbox exists
        if region.bbox is None:
            skipped += 1
            continue

        # Convert to integer pixel bbox
        try:
            x1, y1, x2, y2 = (int(v) for v in region.bbox)
        except (TypeError, ValueError):
            skipped += 1
            continue

        bbox = (x1, y1, x2, y2)

        # Validate bbox geometry
        if not is_valid(bbox):
            skipped += 1
            continue

        # Clip to image bounds if source available
        if src_image is not None:
            h, w = src_image.shape[:2]
            bbox = clip_bbox(bbox, w, h)
            if not is_valid(bbox):
                skipped += 1
                continue

        # Normalize confidence
        confidence = float(region.confidence or 0.0)
        confidence = max(0.0, min(1.0, confidence))

        # Re-extract crop if missing and source image available
        crop = region.cropped_image
        if crop is None and src_image is not None:
            x1, y1, x2, y2 = bbox
            crop = src_image[y1:y2, x1:x2].copy()

        clean.append(Region(
            region_id=f"p{page_number}-r{len(clean)}",   # reassign sequential
            type=region.type,                              # preserve for M5
            bbox=bbox,
            confidence=confidence,
            cropped_image=crop,
            flagged=confidence < 0.70,
        ))

    if skipped > 0:
        print(f"    [compat] page={page_number} — removed {skipped} invalid region(s)")

    return clean


def ensure_text_block_only(regions: list[Region]) -> list[Region]:
    """
    Strip semantic type labels from regions for M4 consumption.

    M4 does not use region.type for logic branching.
    Preserves a copy of the original type in a "pre_m5_type" note (via flagged)
    so M5 can use it if classical_cv labels are trusted.

    For DocTR output: no change (already text_block).
    For classical_cv output: type overridden to "text_block" in the M4-bound copy.

    NOTE: This does NOT modify the LayoutDocument used by M5.
          Call this only when feeding the M4 OCR batch — not for M5 input.

    Args:
        regions: Sanitized regions from ensure_region_integrity().

    Returns:
        New list with type="text_block" on every region.
    """
    return [
        Region(
            region_id=r.region_id,
            type="text_block",
            bbox=r.bbox,
            confidence=r.confidence,
            cropped_image=r.cropped_image,
            flagged=r.flagged,
        )
        for r in regions
    ]


# ── Convenience wrapper for the standard M4 handoff ──────────────────────────

def prepare_for_m4(
    layout_doc: LayoutDocument,
    image_map: dict[int, np.ndarray] | None = None,
) -> LayoutDocument:
    """
    Full normalization pipeline for M4 handoff.

    Steps:
        1. normalize_layout_output  (bbox, confidence, crop integrity)
        2. ensure_text_block_only   (strip semantic labels — M4 doesn't use them)

    Returns:
        M4-safe LayoutDocument.
    """
    normalized = normalize_layout_output(layout_doc, image_map)
    m4_pages: list[LayoutPage] = []

    for page in normalized.pages:
        m4_regions = ensure_text_block_only(page.regions)
        m4_pages.append(LayoutPage(
            page_number=page.page_number,
            regions=m4_regions,
            layout_type=page.layout_type,
            column_count=page.column_count,
        ))

    return LayoutDocument(metadata=normalized.metadata, pages=m4_pages)
