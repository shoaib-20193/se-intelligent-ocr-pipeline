"""
Pure geometric helper utilities for bounding box manipulation.
Coordinates are in (x1, y1, x2, y2) format.
"""
import math

def bbox_area(bbox: tuple[int, int, int, int]) -> int:
    w = max(0, bbox[2] - bbox[0])
    h = max(0, bbox[3] - bbox[1])
    return w * h

def intersection_area(bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]) -> int:
    ix1 = max(bbox1[0], bbox2[0])
    iy1 = max(bbox1[1], bbox2[1])
    ix2 = min(bbox1[2], bbox2[2])
    iy2 = min(bbox1[3], bbox2[3])
    w = max(0, ix2 - ix1)
    h = max(0, iy2 - iy1)
    return w * h

def union_area(bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]) -> int:
    area1 = bbox_area(bbox1)
    area2 = bbox_area(bbox2)
    inter = intersection_area(bbox1, bbox2)
    return area1 + area2 - inter

def iou(bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]) -> float:
    u = union_area(bbox1, bbox2)
    if u == 0:
        return 0.0
    return intersection_area(bbox1, bbox2) / u

def clip_bbox(bbox: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    return (
        max(0, min(bbox[0], width)),
        max(0, min(bbox[1], height)),
        max(0, min(bbox[2], width)),
        max(0, min(bbox[3], height))
    )

def expand_bbox(bbox: tuple[int, int, int, int], padding: int, max_w: int, max_h: int) -> tuple[int, int, int, int]:
    return clip_bbox(
        (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding),
        max_w, max_h
    )

def bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)

def bbox_distance(bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]) -> float:
    """Euclidean distance between the centers of two bounding boxes."""
    cx1, cy1 = bbox_center(bbox1)
    cx2, cy2 = bbox_center(bbox2)
    return math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
