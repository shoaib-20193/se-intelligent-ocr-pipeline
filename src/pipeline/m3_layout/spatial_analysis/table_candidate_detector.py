"""
Table Candidate Detector — identify potential table layouts using geometric regularity.
Strictly spatial/geometric only. No semantic inference. No OCR text.
Sets spatial_metadata["table_candidate"] = True on qualifying regions.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region


def _row_bands(regions: List[Region], v_gap_tolerance: int = 5) -> list[list[Region]]:
    """Group regions into horizontal row bands by vertical proximity."""
    if not regions:
        return []
    sorted_r = sorted(regions, key=lambda r: r.y1)
    rows: list[list[Region]] = [[sorted_r[0]]]
    for r in sorted_r[1:]:
        last_row = rows[-1]
        row_y2 = max(x.y2 for x in last_row)
        if r.y1 <= row_y2 + v_gap_tolerance:
            last_row.append(r)
        else:
            rows.append([r])
    return rows


def _col_bands(regions: List[Region], h_gap_tolerance: int = 5) -> list[list[Region]]:
    """Group regions into vertical column bands by horizontal proximity."""
    if not regions:
        return []
    sorted_r = sorted(regions, key=lambda r: r.x1)
    cols: list[list[Region]] = [[sorted_r[0]]]
    for r in sorted_r[1:]:
        last_col = cols[-1]
        col_x2 = max(x.x2 for x in last_col)
        if r.x1 <= col_x2 + h_gap_tolerance:
            last_col.append(r)
        else:
            cols.append([r])
    return cols


def detect_table_candidates(
    regions: List[Region],
    page_width: int,
    page_height: int,
    min_rows: int = 3,
    min_cols: int = 2,
    regularity_tolerance: float = 0.15,
) -> List[Region]:
    """
    Detect table-candidate region groups via geometric regularity analysis.

    A group qualifies if:
    - It has >= min_rows horizontal bands
    - It has >= min_cols vertical bands
    - Row spacing is roughly regular (coefficient of variation <= regularity_tolerance)
    - Column alignment is consistent

    Returns updated Region objects with spatial_metadata["table_candidate"] set.
    """
    if not regions:
        return regions

    rows = _row_bands(regions)
    cols_in_rows = [_col_bands(row, h_gap_tolerance=max(5, int(page_width * 0.01))) for row in rows]

    # Check row count
    if len(rows) < min_rows:
        return _mark_all(regions, False)

    # Check that most rows have >= min_cols
    rows_with_cols = sum(1 for c in cols_in_rows if len(c) >= min_cols)
    if rows_with_cols < max(min_rows, len(rows) * 0.6):
        return _mark_all(regions, False)

    # Check vertical spacing regularity
    row_tops = [min(r.y1 for r in row) for row in rows]
    gaps = [row_tops[i + 1] - row_tops[i] for i in range(len(row_tops) - 1)]
    if gaps:
        mean_gap = sum(gaps) / len(gaps)
        if mean_gap > 0:
            import math
            variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
            cv = math.sqrt(variance) / mean_gap  # coefficient of variation
            if cv > regularity_tolerance * 3:  # allow looser tolerance
                return _mark_all(regions, False)

    # All checks passed — mark all regions in this group as table candidates
    return _mark_all(regions, True)


def _mark_all(regions: List[Region], is_candidate: bool) -> List[Region]:
    updated = []
    for r in regions:
        new_meta = dict(r.spatial_metadata)
        new_meta["table_candidate"] = is_candidate
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
