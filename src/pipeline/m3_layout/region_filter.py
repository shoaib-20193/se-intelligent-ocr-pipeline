"""
M3 — Region Filter: confidence gating and noise removal.
V3 NEW — agents.md §MODULE_CONTRACTS → M3 Step 2 + §ALGO-CONF

agents.md rules:
    - confidence >= 0.7 → accepted (layout_confidence_threshold = 0.7 per FR-3)
    - confidence in [0.5, 0.7) → flagged, included with warning
    - confidence < 0.5 → discarded (excluded from OCR pipeline)
    - Remove noise boxes below minimum area
    - Merge near-duplicate overlapping boxes (IoU > merge_threshold)
"""
from __future__ import annotations
from src.pipeline.m3_layout.detector import RawDetection
from src.utils.bbox_utils import iou, merge_bboxes, area, is_valid

# ── Confidence band thresholds ─────────────────────────────────────────────────
CONFIDENCE_ACCEPT:  float = 0.70  # agents.md FR-3 LAYOUT_CONFIDENCE_THRESHOLD
CONFIDENCE_WARN:    float = 0.50  # below this → discard
MERGE_IOU_THRESHOLD: float = 0.60  # overlap threshold for near-duplicate merge


def filter_regions(
    detections: list[RawDetection],
    image_w: int,
    image_h: int,
    confidence_threshold: float = CONFIDENCE_ACCEPT,
    merge_iou_threshold: float = MERGE_IOU_THRESHOLD,
) -> list[RawDetection]:
    """
    Apply confidence gating, noise removal, and near-duplicate merging.

    Args:
        detections:          Raw detections from any layout backend.
        image_w, image_h:    Page dimensions in pixels.
        confidence_threshold: Minimum confidence to accept (default 0.7 per FR-3).
        merge_iou_threshold:  IoU above which two boxes are merged.

    Returns:
        Filtered list — discarded boxes removed, near-duplicates merged,
        flagged detections marked but included.
    """
    if not detections:
        return []

    # Step 1: Remove invalid bboxes and extreme noise
    valid = [d for d in detections if is_valid(d.bbox)]

    # Step 2: Remove tiny boxes (area < 0.05% of page)
    min_area = image_w * image_h * 0.0005
    valid = [d for d in valid if area(d.bbox) >= min_area]

    # Step 3: Merge near-duplicate overlapping boxes (greedy)
    valid = _merge_overlapping(valid, merge_iou_threshold)

    # Step 4: Confidence gating (agents.md §ALGO-CONF)
    result: list[RawDetection] = []
    for det in valid:
        if det.confidence >= confidence_threshold:
            result.append(det)   # fully accepted
        elif det.confidence >= CONFIDENCE_WARN:
            # Flag and include (will be marked on Region.flagged)
            flagged = RawDetection(
                bbox=det.bbox,
                confidence=det.confidence,
                raw_type=f"flagged_{det.raw_type}",
            )
            result.append(flagged)
        # else: silently discard (confidence < 0.5)

    return result


def _merge_overlapping(
    detections: list[RawDetection],
    iou_threshold: float,
) -> list[RawDetection]:
    """
    Greedy IoU-based merge: if two boxes overlap above threshold, merge into one.
    The merged box takes the higher confidence value.
    """
    if not detections:
        return []

    # Sort by area descending (larger boxes are primary; small ones absorbed first)
    boxes = sorted(detections, key=lambda d: area(d.bbox), reverse=True)
    merged: list[RawDetection] = []
    used = [False] * len(boxes)

    for i, primary in enumerate(boxes):
        if used[i]:
            continue
        group_bboxes = [primary.bbox]
        group_conf   = primary.confidence

        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            if iou(primary.bbox, boxes[j].bbox) >= iou_threshold:
                group_bboxes.append(boxes[j].bbox)
                group_conf = max(group_conf, boxes[j].confidence)
                used[j] = True

        merged_bbox = merge_bboxes(group_bboxes) if len(group_bboxes) > 1 else primary.bbox
        merged.append(RawDetection(
            bbox=merged_bbox,
            confidence=group_conf,
            raw_type=primary.raw_type,
        ))
        used[i] = True

    return merged
