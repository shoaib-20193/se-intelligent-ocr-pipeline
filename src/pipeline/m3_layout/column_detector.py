"""
M3 — Column Detector: x-projection based single/multi-column classification.
V3 NEW — agents.md §MODULE_CONTRACTS → M3 Step 6 + §ALGO-RO

Algorithm (x-projection clustering):
    1. Project all region bboxes onto the x-axis (create binary x-occupancy array)
    2. Find contiguous occupied bands (clusters of non-zero x values)
    3. Count clusters with significant width → column count
    4. Classify: N=1 → single_column; N=2 → multi_column (2-col); N>2 → multi_column (N-col)

Special case: if all regions span > 60% of page width → single column layout,
regardless of cluster analysis.
"""
from __future__ import annotations
import numpy as np
from src.pipeline.m3_layout.detector import RawDetection

# ── Tuning constants ───────────────────────────────────────────────────────────
_FULL_WIDTH_FRAC: float = 0.60   # region wider than this → full-width (header/footer, not column)
_MIN_COLUMN_WIDTH: int  = 40      # minimum pixels for a cluster to count as a column
_COLUMN_GAP_MIN:   int  = 15      # minimum pixel gap to split into separate columns


def detect_columns(
    detections: list[RawDetection],
    image_w: int,
    image_h: int,
) -> tuple[str, int]:
    """
    Classify document layout from detected regions.

    Args:
        detections: Filtered region list (after region_filter.py).
        image_w:    Page width in pixels.
        image_h:    Page height in pixels.

    Returns:
        (layout_type, column_count)
        layout_type:  "single_column" | "multi_column"
        column_count: 1, 2, 3, …
    """
    if not detections:
        return "single_column", 1

    # Exclude full-width regions from column analysis (they're headers/footers/dividers)
    body_regions = [
        d for d in detections
        if (d.bbox[2] - d.bbox[0]) < image_w * _FULL_WIDTH_FRAC
    ]

    if not body_regions:
        # All regions are full-width → likely single-column with headers only
        return "single_column", 1

    # Build x-occupancy array
    occupancy = np.zeros(image_w, dtype=np.uint8)
    for det in body_regions:
        x1, _, x2, _ = det.bbox
        x1 = max(0, x1)
        x2 = min(image_w, x2)
        occupancy[x1:x2] = 1

    # Find contiguous occupied bands
    clusters = _find_clusters(occupancy, min_width=_MIN_COLUMN_WIDTH, min_gap=_COLUMN_GAP_MIN)
    column_count = len(clusters)

    if column_count <= 1:
        return "single_column", 1
    else:
        return "multi_column", column_count


def get_column_bands(
    detections: list[RawDetection],
    image_w: int,
    column_count: int,
) -> list[tuple[int, int]]:
    """
    Compute x-coordinate boundaries for each column band.
    Used by reading_order.py for band-sort.

    Returns:
        List of (x_start, x_end) tuples, one per column, sorted left→right.
    """
    if column_count <= 1:
        return [(0, image_w)]

    # Divide page width equally into column_count bands
    band_width = image_w // column_count
    return [(i * band_width, (i + 1) * band_width) for i in range(column_count)]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _find_clusters(
    occupancy: np.ndarray,
    min_width: int,
    min_gap: int,
) -> list[tuple[int, int]]:
    """
    Find contiguous occupied runs in a 1D binary array.
    Returns list of (start, end) index pairs for runs with width >= min_width.
    Runs separated by < min_gap pixels are merged.
    """
    clusters: list[tuple[int, int]] = []
    in_cluster = False
    start = 0

    for i, val in enumerate(occupancy):
        if val > 0 and not in_cluster:
            in_cluster = True
            start = i
        elif val == 0 and in_cluster:
            in_cluster = False
            width = i - start
            if width >= min_width:
                clusters.append((start, i))

    if in_cluster:
        width = len(occupancy) - start
        if width >= min_width:
            clusters.append((start, len(occupancy)))

    # Merge clusters separated by gaps smaller than min_gap
    clusters = _merge_close_clusters(clusters, min_gap)

    return clusters


def _merge_close_clusters(
    clusters: list[tuple[int, int]],
    min_gap: int,
) -> list[tuple[int, int]]:
    """Merge adjacent clusters with gap < min_gap."""
    if not clusters:
        return []
    merged = [clusters[0]]
    for start, end in clusters[1:]:
        prev_start, prev_end = merged[-1]
        if start - prev_end < min_gap:
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))
    return merged
