"""
M3 — Semantic Grouper: heuristic rule-based region type classification.
V3 NEW — agents.md §MODULE_CONTRACTS → M3 Step 9

Output type enum (agents.md §DATA_MODEL → Region.type):
    "header"    — heading text (title, section heading)
    "paragraph" — body text
    "table"     — tabular data region
    "figure"    — image, chart, diagram
    "footer"    — page footer text

Classification rules (all positional + geometric — no OCR):

    header:     top 18% of page AND (wide region OR tall bbox relative to width)
    footer:     bottom 10% of page
    table:      aspect ratio roughly square to 4:1 AND not header/footer position
                AND presence of horizontal/vertical projection regularity
    figure:     large area (> 8% page) AND aspect ratio not matching text blocks
    paragraph:  default (everything else)
"""
from __future__ import annotations
import cv2
import numpy as np
from src.data_model.layout import Region

# ── Position thresholds (fraction of page height) ──────────────────────────────
_HEADER_ZONE: float = 0.18   # top 18% → header candidate
_FOOTER_ZONE: float = 0.10   # bottom 10% → footer candidate

# ── Size thresholds ────────────────────────────────────────────────────────────
_FIGURE_MIN_PAGE_FRAC: float = 0.06   # > 6% of page area → figure candidate
_FULL_WIDTH_FRAC:      float = 0.55   # > 55% of page width → "wide" region

# ── Table detection thresholds ─────────────────────────────────────────────────
_TABLE_MIN_ASPECT: float = 1.0    # min width/height ratio
_TABLE_MAX_ASPECT: float = 8.0    # max width/height ratio
_TABLE_MIN_AREA_FRAC: float = 0.02  # > 2% of page


def assign_semantics(
    regions: list[Region],
    image: np.ndarray,
    page_width: int,
    page_height: int,
) -> list[Region]:
    """
    Assign semantic type to each region in-place.
    Operates in a single prioritised pass per region.

    Priority order (first matching rule wins):
        1. header  (position-based)
        2. footer  (position-based)
        3. figure  (area + aspect ratio)
        4. table   (aspect ratio + projection regularity, with image evidence)
        5. paragraph (default)

    DOES NOT modify image pixels — image is read-only for table evidence.

    Args:
        regions:      Region list (any type value, will be overwritten).
        image:        Grayscale or BGR uint8 ndarray (source of truth for table detection).
        page_width:   Page width in pixels.
        page_height:  Page height in pixels.

    Returns:
        The same list with Region.type updated in-place.
    """
    page_area = max(page_width * page_height, 1)

    for region in regions:
        region.type = _classify(region, image, page_width, page_height, page_area)

    return regions


def _classify(
    region: Region,
    image: np.ndarray,
    page_width: int,
    page_height: int,
    page_area: int,
) -> str:
    x1, y1, x2, y2 = region.bbox
    rw  = x2 - x1
    rh  = y2 - y1
    ra  = rw * rh
    aspect = rw / max(rh, 1)
    top_frac = y1 / max(page_height, 1)
    bot_frac = y2 / max(page_height, 1)
    width_frac = rw / max(page_width, 1)

    # ── Rule 1: Header ──────────────────────────────────────────────────────────
    # Top zone + (wide span OR tall-for-width suggests large text)
    if top_frac < _HEADER_ZONE:
        if width_frac > _FULL_WIDTH_FRAC or aspect > 6:
            return "header"

    # ── Rule 2: Footer ──────────────────────────────────────────────────────────
    if bot_frac > (1 - _FOOTER_ZONE):
        return "footer"

    # ── Rule 3: Figure ──────────────────────────────────────────────────────────
    # Large region with non-text-like aspect ratio
    area_frac = ra / page_area
    if area_frac > _FIGURE_MIN_PAGE_FRAC:
        # Text blocks usually have aspect > 2; figures can be squarish or very wide
        if aspect < 1.5 or aspect > 20:
            return "figure"

    # ── Rule 4: Table ───────────────────────────────────────────────────────────
    area_frac = ra / page_area
    if area_frac >= _TABLE_MIN_AREA_FRAC:
        if _TABLE_MIN_ASPECT <= aspect <= _TABLE_MAX_ASPECT:
            if _has_table_evidence(image, region.bbox):
                return "table"

    # ── Rule 5: Paragraph (default) ─────────────────────────────────────────────
    return "paragraph"


def _has_table_evidence(image: np.ndarray, bbox: tuple[int, int, int, int]) -> bool:
    """
    Heuristic table detector: check for projection regularity within region crop.

    A table tends to have multiple roughly equal-height text rows with visible
    horizontal gaps. We detect this via horizontal projection of the binary image:
    a table crop will show alternating high/low density bands (rows vs gaps).

    Returns True if the region shows table-like banding.
    """
    x1, y1, x2, y2 = bbox
    if len(image.shape) == 3:
        crop = cv2.cvtColor(image[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    else:
        crop = image[y1:y2, x1:x2].copy()

    if crop.size == 0:
        return False

    # Binarise crop
    if len(np.unique(crop)) > 2:
        _, binary = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        binary = crop if crop.mean() < 127 else cv2.bitwise_not(crop)

    # Horizontal projection (sum of white pixels per row)
    h_proj = binary.sum(axis=1).astype(np.float32)
    if h_proj.max() == 0:
        return False

    h_proj /= h_proj.max()  # normalize

    # Count zero-crossings from high (> 0.1) to low (< 0.05)
    # Regular tables have many alternating text-row / gap pairs
    crossings = 0
    above = h_proj[0] > 0.1
    for val in h_proj[1:]:
        now_above = val > 0.1
        if above != now_above:
            crossings += 1
            above = now_above

    # If height of region > 50px and crossings > 6 → likely table
    region_h = y2 - y1
    if region_h > 50 and crossings >= 6:
        return True

    return False
