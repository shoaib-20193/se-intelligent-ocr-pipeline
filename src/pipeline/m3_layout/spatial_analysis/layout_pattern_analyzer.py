"""
Layout Pattern Analyzer — determine page layout pattern from column/region geometry.
Strictly spatial/geometric only. No semantic inference.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region


def analyze_layout_pattern(
    regions: List[Region],
    column_count: int,
    page_width: int,
    page_height: int,
    multi_col_threshold: int = 2,
) -> str:
    """
    Determine the layout type of the page from spatial structure.

    Returns:
        "structured_columns": clear multi-column layout detected
        "raw_blocks":         single-column or ambiguous layout
    """
    if not regions:
        return "raw_blocks"

    if column_count >= multi_col_threshold:
        return "structured_columns"

    # Secondary check: look for horizontally segregated regions even if gap wasn't caught
    if page_width > 0:
        left_count = sum(1 for r in regions if r.center_x < page_width * 0.4)
        right_count = sum(1 for r in regions if r.center_x > page_width * 0.6)
        centre_count = len(regions) - left_count - right_count
        # If significant proportion of regions are clearly left/right-split
        if left_count >= 2 and right_count >= 2 and centre_count < (len(regions) * 0.2):
            return "structured_columns"

    return "raw_blocks"
