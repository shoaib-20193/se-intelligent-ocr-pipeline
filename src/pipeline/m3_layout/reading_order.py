"""
M3 — Reading Order: §ALGO-RO band-sort implementation.
V3 NEW — agents.md §CORE_ALGORITHMS → §ALGO-RO

Canonical algorithm (agents.md §ALGO-RO):

    Input:  list[Region] for a single page; page_width: int
    Steps (deterministic):
        1. If single-column (all regions: x1 < page_width * 0.6): form one group
        2. Otherwise divide page into N equal vertical bands (N = detected column count):
            For N=2: LEFT = x1 < page_width/2; RIGHT = x1 >= page_width/2
            For N>2: band_width = page_width / N; band_index = floor(region.x1 / band_width)
        3. Within each band: sort regions by y1 ascending
        4. Concatenate bands left → right
    Output: list[Region] in reading order

Implementation note: this module operates on Region objects, not RawDetections.
It is called AFTER regions have been converted and semantically grouped.
"""
from __future__ import annotations
import math
from src.data_model.layout import Region


def compute_reading_order(
    regions: list[Region],
    page_width: int,
    column_count: int,
) -> list[Region]:
    """
    Sort regions into reading order using the §ALGO-RO band-sort algorithm.

    DETERMINISTIC: for identical inputs, output order is always identical.
    Tie-breaking: regions with equal y1 are sorted by x1 (left before right).

    Args:
        regions:      List of Region objects (any order).
        page_width:   Page width in pixels.
        column_count: Number of detected columns (1 = single-column path).

    Returns:
        New list of the same Region objects in reading order.
        Original list is not modified.
    """
    if not regions:
        return []

    if column_count <= 1:
        # §ALGO-RO Step 1: single column → sort all by y1
        return _sort_by_y(regions)

    # §ALGO-RO Steps 2–4: multi-column band sort
    return _band_sort(regions, page_width, column_count)


def _sort_by_y(regions: list[Region]) -> list[Region]:
    """Sort regions top-to-bottom, left-to-right within same y position."""
    return sorted(regions, key=lambda r: (r.y1, r.x1))


def _band_sort(
    regions: list[Region],
    page_width: int,
    column_count: int,
) -> list[Region]:
    """
    §ALGO-RO multi-column: divide into N equal bands, sort each by y1,
    then concatenate bands left→right.
    """
    bands: dict[int, list[Region]] = {i: [] for i in range(column_count)}

    if column_count == 2:
        # Canonical 2-column split at page midpoint
        mid = page_width / 2
        for region in regions:
            band_idx = 0 if region.x1 < mid else 1
            bands[band_idx].append(region)
    else:
        # N-column: equal-width bands
        band_width = page_width / column_count
        for region in regions:
            band_idx = min(int(math.floor(region.x1 / band_width)), column_count - 1)
            bands[band_idx].append(region)

    # Sort within each band by y1, then concatenate left → right
    ordered: list[Region] = []
    for band_idx in range(column_count):
        ordered.extend(_sort_by_y(bands[band_idx]))

    return ordered
