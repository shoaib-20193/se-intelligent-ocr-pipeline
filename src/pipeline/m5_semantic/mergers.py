"""
src/pipeline/m5_semantic/mergers.py
Implements token merging algorithms to reduce OCR fragmentation.
Uses M3 authoritative bbox — geometry is NEVER recomputed during merges.
"""
from typing import List
from src.pipeline.m5_semantic.contracts import SemanticSpatialToken, BoundingBox


def merge_tokens(tokens: List[SemanticSpatialToken], vertical_threshold: int = 20) -> List[SemanticSpatialToken]:
    """
    Merges adjacent paragraph tokens to improve readability.
    Assumes tokens are pre-sorted in reading order.
    
    CRITICAL RULE: When merging, the PRIMARY token's bbox is preserved.
    We do NOT union bounding boxes — M3 is the spatial authority.
    """
    if not tokens:
        return []

    merged = []
    current = tokens[0]

    for next_token in tokens[1:]:
        # Criteria for merging
        # 1. Must be the same type and must be paragraphs
        is_same_type = current.block_type == next_token.block_type
        is_paragraph = current.block_type == "paragraph"
        
        # 2. Structural compatibility check
        def can_merge_structurally(a: SemanticSpatialToken, b: SemanticSpatialToken) -> bool:
            if a.spatial_metadata.get("column_id") != b.spatial_metadata.get("column_id"):
                return False
            if a.spatial_metadata.get("cluster_id") != b.spatial_metadata.get("cluster_id"):
                return False
            if a.spatial_metadata.get("table_candidate") != b.spatial_metadata.get("table_candidate"):
                return False
            return True
            
        structurally_compatible = can_merge_structurally(current, next_token)
        
        # Calculate vertical gap (distance from bottom of current to top of next)
        vertical_gap = next_token.bbox.y_min - current.bbox.y_max

        # We merge if they overlap vertically or are very close, and they are structurally compatible
        if is_same_type and is_paragraph and structurally_compatible and vertical_gap < vertical_threshold:
            # Construct merged fields — text only, bbox from primary (current)
            new_text = current.text.strip() + " " + next_token.text.strip()
            
            # Merge spatial metadata from primary
            new_spatial_metadata = current.spatial_metadata.copy()
            
            # Create the merged token, preserving the FIRST token's bbox (M3 authoritative)
            current = SemanticSpatialToken(
                token_id=current.token_id,
                text=new_text,
                block_type="paragraph",
                bbox=current.bbox,  # M3 authoritative — NEVER recomputed
                confidence=(current.confidence + next_token.confidence) / 2.0,
                reading_order=current.reading_order,
                page_number=current.page_number,
                source_region_id=current.source_region_id,
                spatial_metadata=new_spatial_metadata
            )
        else:
            merged.append(current)
            current = next_token
            
    merged.append(current)
    return merged
