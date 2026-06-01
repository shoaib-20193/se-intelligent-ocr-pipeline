"""
src/pipeline/m3_layout/spatial_analysis/column_detector.py
Column Detector — detect multi-column layouts using density cluster analysis.
Upgraded with fuzzy boundary tolerance and neighbor alignment strength
to prevent column bleed from noisy OCR coordinates.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region

FUZZY_MARGIN_RATIO = 0.015


def _build_x_projection(regions: List[Region], page_width: int) -> list[int]:
    """Build a histogram of horizontal region coverage, binned by pixel column."""
    histogram = [0] * max(1, page_width)
    for r in regions:
        # Weight by confidence if available, else 1
        weight = int(r.confidence * 10) if r.confidence > 0 else 5
        x1, _, x2, _ = r.bbox
        for x in range(int(max(0, x1)), int(min(x2, page_width))):
            histogram[x] += weight
    return histogram


def _find_valley_gaps(histogram: list[int], threshold: int = 0, min_gap_width: int = 10) -> list[tuple[int, int]]:
    """Find contiguous zero/low-activity x-ranges (inter-column gutters)."""
    gaps = []
    start = None
    for x, val in enumerate(histogram):
        if val <= threshold:
            if start is None:
                start = x
        else:
            if start is not None and (x - start) >= min_gap_width:
                gaps.append((start, x - 1))
            start = None
    if start is not None and (len(histogram) - start) >= min_gap_width:
        gaps.append((start, len(histogram) - 1))
    return gaps


def detect_columns(regions: List[Region], page_width: int, page_height: int,
                   min_gap_fraction: float = 0.01) -> tuple[int, list[int]]:
    """
    Detect column count and boundaries via density-cluster histogram.
    """
    if not regions or page_width <= 0:
        return 1, []

    min_gap_px = max(5, int(page_width * min_gap_fraction))
    histogram = _build_x_projection(regions, page_width)
    
    # Use a slight threshold instead of 0 to tolerate noise in gutters
    avg_density = sum(histogram) / max(len(histogram), 1)
    noise_threshold = avg_density * 0.05
    
    gaps = _find_valley_gaps(histogram, threshold=noise_threshold, min_gap_width=min_gap_px)

    if not gaps:
        return 1, []

    # Column boundaries are the midpoints of each gap
    boundaries = [(g[0] + g[1]) // 2 for g in gaps]
    column_count = len(boundaries) + 1
    return column_count, boundaries


def assign_column_ids(regions: List[Region], column_boundaries: list[int], page_width: int) -> list[int]:
    """
    Determine which column a region belongs to.
    Uses fuzzy boundary tolerance: if a region falls on the boundary line,
    it looks at neighbor alignment to decide.
    """
    if not column_boundaries:
        return [0] * len(regions)
        
    column_ids = []
    fuzzy_margin = page_width * FUZZY_MARGIN_RATIO

    for i, r in enumerate(regions):
        x1, _, x2, _ = r.bbox
        cx = (x1 + x2) / 2.0
        
        # Check against boundaries
        assigned = False
        for col_idx, boundary in enumerate(column_boundaries):
            if cx < boundary - fuzzy_margin:
                column_ids.append(col_idx)
                assigned = True
                break
            elif abs(cx - boundary) <= fuzzy_margin:
                # Fuzzy zone! Use neighbor alignment strength.
                # Is the box mostly left or right of the boundary?
                left_area = max(0, boundary - x1)
                right_area = max(0, x2 - boundary)
                
                if left_area > right_area * 1.5:
                    column_ids.append(col_idx)
                elif right_area > left_area * 1.5:
                    column_ids.append(col_idx + 1)
                else:
                    # Look at nearest vertical neighbors
                    nearest_col = _infer_from_vertical_neighbors(i, regions, col_idx, column_boundaries, fuzzy_margin)
                    column_ids.append(nearest_col)
                assigned = True
                break
                
        if not assigned:
            # Must be the last column
            column_ids.append(len(column_boundaries))
            
    return column_ids


def _infer_from_vertical_neighbors(region_idx: int, regions: List[Region], boundary_idx: int, boundaries: list[int], fuzzy_margin: float) -> int:
    """Uses vertical continuity to resolve fuzzy column boundaries."""
    target_r = regions[region_idx]
    _, ty1, _, ty2 = target_r.bbox
    t_cy = (ty1 + ty2) / 2.0
    boundary = boundaries[boundary_idx]
    
    # Find closest vertical neighbor
    closest_dist = float('inf')
    vote = boundary_idx  # default left
    
    for i, r in enumerate(regions):
        if i == region_idx: continue
        x1, y1, x2, y2 = r.bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        
        # Only care about neighbors firmly established in a column
        if abs(cx - boundary) > fuzzy_margin:
            v_dist = abs(t_cy - cy)
            if v_dist < closest_dist and v_dist < 200:
                closest_dist = v_dist
                vote = boundary_idx if cx < boundary else boundary_idx + 1
                
    return vote
