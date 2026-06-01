"""
Compat Layer — DTO normalization for layout backends.
Normalizes Region objects to ensure full V3.2 DTO compliance.
FORBIDDEN: semantic enrichment, reading-order mutation, region merging,
           semantic classification, document reconstruction.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region, LayoutPage, LayoutDocument


_FORBIDDEN_SPATIAL_KEYS = {
    "header", "footer", "title", "section", "caption", "semantic_class",
    "paragraph_type", "section_type", "heading_level",
}

_REQUIRED_SPATIAL_KEYS = {
    "reading_order", "cluster_id", "column_id",
    "adjacency_links", "table_candidate", "paragraph_candidate", "spatial_group_id",
}


def _validate_and_normalize_region(region: Region) -> Region:
    """
    Ensure a Region object is fully V3.2 compliant:
    - type must equal "text_block"
    - spatial_metadata must contain no forbidden semantic keys
    - spatial_metadata defaults are filled in if missing
    """
    if region.type != "text_block":
        raise ValueError(
            f"[compat_layer] V3.2 VIOLATION: Region '{region.id}' has type='{region.type}'. "
            f"Only 'text_block' is permitted in M3."
        )

    new_meta = dict(region.spatial_metadata)

    # Check for forbidden semantic keys
    leaked_keys = _FORBIDDEN_SPATIAL_KEYS.intersection(new_meta.keys())
    if leaked_keys:
        raise ValueError(
            f"[compat_layer] V3.2 SEMANTIC LEAKAGE DETECTED in Region '{region.id}': "
            f"forbidden keys found in spatial_metadata: {leaked_keys}"
        )

    # Fill in missing required keys with safe defaults
    new_meta.setdefault("reading_order", -1)
    new_meta.setdefault("cluster_id", -1)
    new_meta.setdefault("column_id", 0)
    new_meta.setdefault("adjacency_links", [])
    new_meta.setdefault("table_candidate", False)
    new_meta.setdefault("paragraph_candidate", False)
    new_meta.setdefault("spatial_group_id", -1)

    return Region(
        id=region.id,
        bbox=region.bbox,
        polygon=region.polygon,
        confidence=region.confidence,
        type="text_block",
        spatial_metadata=new_meta,
        crop_ref=region.crop_ref,
    )


def normalize_layout_document(doc: LayoutDocument) -> LayoutDocument:
    """
    Validate and normalize all Region objects in a LayoutDocument.
    Raises ValueError on any V3.2 architectural violation.
    Returns a fully normalized LayoutDocument.
    """
    normalized_pages = []
    for page in doc.pages:
        normalized_regions = [_validate_and_normalize_region(r) for r in page.regions]
        normalized_pages.append(LayoutPage(
            page_number=page.page_number,
            regions=normalized_regions,
            layout_type=page.layout_type,
            column_count=page.column_count,
            metadata=page.metadata,
        ))
    return LayoutDocument(
        document_id=doc.document_id,
        metadata=doc.metadata,
        pages=normalized_pages,
        processing_metadata=doc.processing_metadata,
    )
