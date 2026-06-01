"""
Convert normalized coordinates to absolute integer coordinates.
"""
from typing import Optional

def normalize_bbox(rel_bbox: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    """
    Convert (xmin, ymin, xmax, ymax) in [0, 1] to absolute integer coordinates,
    clipped to image dimensions.
    """
    x1 = max(0, min(int(round(rel_bbox[0] * width)), width))
    y1 = max(0, min(int(round(rel_bbox[1] * height)), height))
    x2 = max(0, min(int(round(rel_bbox[2] * width)), width))
    y2 = max(0, min(int(round(rel_bbox[3] * height)), height))
    
    # Ensure x1 <= x2 and y1 <= y2
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

def normalize_polygon(rel_polygon: list[tuple[float, float]], width: int, height: int) -> list[tuple[int, int]]:
    """
    Convert a list of (x, y) relative points to absolute integer coordinates.
    """
    return [
        (
            max(0, min(int(round(pt[0] * width)), width)),
            max(0, min(int(round(pt[1] * height)), height))
        )
        for pt in rel_polygon
    ]
