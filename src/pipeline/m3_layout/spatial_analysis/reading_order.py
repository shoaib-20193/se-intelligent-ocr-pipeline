"""
Reading Order — deterministic stable reading-order resolution.
Strictly spatial/geometric. No semantic inference.
Sort key: (column_id, y1, x1, area, region_id) — stable and deterministic.
Populates spatial_metadata["reading_order"].
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region


def resolve_reading_order(regions: List[Region]) -> List[Region]:
    """
    Sort regions into reading order and assign spatial_metadata["reading_order"].

    Sort key (stable):
      1. column_id  (left columns before right)
      2. y1         (top before bottom)
      3. x1         (left before right within same band)
      4. area       (larger regions first on ties)
      5. region_id  (final tiebreak for full determinism)

    Returns new Region objects with reading_order populated.
    Original regions are NOT mutated.
    """
    if not regions:
        return []

    def sort_key(r: Region) -> tuple:
        col_id = r.spatial_metadata.get("column_id", 0)
        return (col_id, r.y1, r.x1, -r.area, r.id)

    sorted_regions = sorted(regions, key=sort_key)

    result = []
    for order_idx, r in enumerate(sorted_regions):
        new_meta = dict(r.spatial_metadata)
        new_meta["reading_order"] = order_idx
        result.append(Region(
            id=r.id,
            bbox=r.bbox,
            polygon=r.polygon,
            confidence=r.confidence,
            type="text_block",
            spatial_metadata=new_meta,
            crop_ref=r.crop_ref,
        ))
    return result
