"""
Paragraph Cluster — group vertically adjacent, horizontally aligned line-level regions.
Strictly spatial/geometric only. No semantic inference. No NLP. No OCR text.
Sets spatial_metadata["paragraph_candidate"] = True on grouped regions.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region


def _vertical_gap(r_above: Region, r_below: Region) -> int:
    """Gap in pixels between the bottom of r_above and the top of r_below."""
    return r_below.y1 - r_above.y2


def _left_aligned(r1: Region, r2: Region, tolerance_px: int) -> bool:
    return abs(r1.x1 - r2.x1) <= tolerance_px


def _right_aligned(r1: Region, r2: Region, tolerance_px: int) -> bool:
    return abs(r1.x2 - r2.x2) <= tolerance_px


def cluster_paragraphs(
    regions: List[Region],
    page_width: int,
    max_gap_fraction: float = 0.03,
    align_tolerance_fraction: float = 0.05,
    same_column_only: bool = True,
) -> List[Region]:
    """
    Group vertically adjacent, horizontally aligned regions as paragraph candidates.
    Returns new Region objects with updated spatial_metadata.
    Original regions are NOT mutated.
    """
    if not regions:
        return regions

    max_gap_px = max(4, int(page_width * max_gap_fraction))
    align_tol_px = max(4, int(page_width * align_tolerance_fraction))

    # Sort top-to-bottom, left-to-right within same column
    sorted_regions = sorted(regions, key=lambda r: (
        r.spatial_metadata.get("column_id", 0), r.y1, r.x1
    ))

    group_ids: dict[str, int] = {}
    group_counter = 0
    used: set[str] = set()

    for i, r in enumerate(sorted_regions):
        if r.id in used:
            continue
        current_group = group_counter
        group_counter += 1
        group_ids[r.id] = current_group
        used.add(r.id)

        for j in range(i + 1, len(sorted_regions)):
            candidate = sorted_regions[j]
            if candidate.id in used:
                continue
            # Must be in same column
            if same_column_only:
                if r.spatial_metadata.get("column_id", 0) != candidate.spatial_metadata.get("column_id", 0):
                    continue
            # Vertical gap
            gap = _vertical_gap(r, candidate)
            if gap < 0 or gap > max_gap_px:
                break  # sorted by y1, so no more close candidates below
            # Alignment check
            if not (_left_aligned(r, candidate, align_tol_px) or _right_aligned(r, candidate, align_tol_px)):
                continue
            group_ids[candidate.id] = current_group
            used.add(candidate.id)

    # Determine which groups have > 1 member (actual paragraph candidates)
    from collections import Counter
    group_sizes = Counter(group_ids.values())

    # Build updated regions with spatial_metadata
    updated = []
    for r in regions:
        gid = group_ids.get(r.id, -1)
        is_para_candidate = gid >= 0 and group_sizes[gid] > 1
        new_meta = dict(r.spatial_metadata)
        new_meta["paragraph_candidate"] = is_para_candidate
        new_meta["spatial_group_id"] = gid
        updated.append(Region(
            id=r.id,
            bbox=r.bbox,
            polygon=r.polygon,
            confidence=r.confidence,
            type="text_block",
            spatial_metadata=new_meta,
            crop_ref=r.crop_ref,
        ))
    return updated
