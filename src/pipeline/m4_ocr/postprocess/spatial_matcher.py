"""
src/pipeline/m4_ocr/postprocess/spatial_matcher.py
Maps M4 OCR boxes back onto canonical M3 semantic layout regions.
M3 owns the geometry. M4 attaches text only.
"""
import uuid
from typing import List, Tuple
from src.data_model.layout import Region
from src.data_model.ocr import RecognizedRegion


def _compute_centroid(box: List[List[float]]) -> Tuple[float, float]:
    """Computes centroid of a 4-point polygon (PaddleOCR format)."""
    x_coords = [p[0] for p in box]
    y_coords = [p[1] for p in box]
    return (sum(x_coords) / 4.0, sum(y_coords) / 4.0)


def _contains_centroid(bbox: Tuple[int, int, int, int], centroid: Tuple[float, float]) -> bool:
    """Checks if a bounding box contains a point."""
    x1, y1, x2, y2 = bbox
    cx, cy = centroid
    return x1 <= cx <= x2 and y1 <= cy <= y2


def match_ocr_to_regions(
    ocr_results: List[Tuple[List[List[float]], Tuple[str, float]]],
    m3_regions: List[Region]
) -> List[RecognizedRegion]:
    """
    Maps OCR full-page results back into canonical M3 regions.
    M3 owns the geometry and semantic labels. M4 just attaches text.
    Region.id is the canonical identifier (not region_id).
    """
    # Create a mapping of M3 region id -> list of matched (text, conf)
    # Region uses .id field per data_model/layout.py
    matched_text_map = {r.id: [] for r in m3_regions}

    for box, (text, conf) in ocr_results:
        if not text.strip():
            continue

        centroid = _compute_centroid(box)

        # Find which M3 region contains this OCR centroid
        for region in m3_regions:
            if _contains_centroid(region.bbox, centroid):
                matched_text_map[region.id].append((text, conf))
                break
        # Strict: discard OCR boxes that fall outside all M3 regions (noise)

    # Reconstruct RecognizedRegions strictly adhering to M3 geometry and order
    recognized_regions = []

    for idx, region in enumerate(m3_regions):
        matched_items = matched_text_map[region.id]
        reading_order = region.spatial_metadata.get("reading_order", idx)

        if matched_items:
            combined_text = " ".join(item[0] for item in matched_items)
            avg_conf = sum(item[1] for item in matched_items) / len(matched_items)
        else:
            combined_text = ""
            avg_conf = 0.0

        rec_region = RecognizedRegion(
            id=str(uuid.uuid4()),
            bbox=region.bbox,
            text=combined_text,
            confidence=avg_conf,
            source_region_id=region.id,
            reading_order=reading_order,
            crop_ref=region.crop_ref,
            spatial_metadata=region.spatial_metadata,
        )
        recognized_regions.append(rec_region)

    return recognized_regions
