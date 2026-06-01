"""
M3 — Box Merger: IoU-based near-duplicate region merge. §ALGO-BB.
V3 NEW — agents.md §CORE_ALGORITHMS → §ALGO-BB

Operates on Region objects (post-assignment), unlike region_filter._merge_overlapping
which operates on RawDetections. This stage handles residual near-duplicates that
survived filtering and semantic grouping.

agents.md §ALGO-BB rules:
    - Merge boxes with IoU > iou_threshold (default 0.55)
    - Merged box inherits: max confidence, type of higher-confidence original
    - region_id reassigned after merge (p{page}-r{new_idx})
"""
from __future__ import annotations
from src.data_model.layout import Region
from src.utils.bbox_utils import iou, merge_bboxes, area

_DEFAULT_IOU_THRESHOLD: float = 0.55


def merge_regions(
    regions: list[Region],
    iou_threshold: float = _DEFAULT_IOU_THRESHOLD,
    page_number: int = 1,
) -> list[Region]:
    """
    Merge overlapping Region objects with IoU above threshold.

    Merge policy:
        - bbox:        convex hull of all merged bboxes
        - type:        inherited from highest-confidence original
        - confidence:  max of merged originals
        - flagged:     True if ANY original was flagged
        - cropped_image: None (will be re-extracted by M3 after merge)

    Args:
        regions:       Input Region list (any order).
        iou_threshold: Merge trigger (default 0.55 per agents.md §ALGO-BB).
        page_number:   For reassigning region_ids after merge.

    Returns:
        New list of Region objects with near-duplicates merged.
        region_ids are reassigned sequentially: p{page}-r{0}, p{page}-r{1}, …
    """
    if not regions:
        return []

    # Sort by area descending — larger regions are primary absorbers
    boxes = sorted(regions, key=lambda r: r.area, reverse=True)
    used = [False] * len(boxes)
    merged_regions: list[Region] = []

    for i, primary in enumerate(boxes):
        if used[i]:
            continue

        group: list[Region] = [primary]

        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            if iou(primary.bbox, boxes[j].bbox) >= iou_threshold:
                group.append(boxes[j])
                used[j] = True

        used[i] = True

        if len(group) == 1:
            merged_regions.append(primary)
        else:
            # Merge group into one region
            all_bboxes = [r.bbox for r in group]
            best = max(group, key=lambda r: r.confidence)
            merged_bbox = merge_bboxes(all_bboxes)
            merged_regions.append(Region(
                region_id="pending",    # will be reassigned below
                type=best.type,
                bbox=merged_bbox,
                confidence=max(r.confidence for r in group),
                cropped_image=None,     # will be re-extracted by interface.py
                flagged=any(r.flagged for r in group),
            ))

    # Reassign region_ids sequentially
    for idx, region in enumerate(merged_regions):
        region.region_id = f"p{page_number}-r{idx}"

    return merged_regions
