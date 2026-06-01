"""
src/pipeline/m6_export/contracts.py
Defines the canonical output contract (RenderableDocument) for M6.
This is the only data structure PyQt6 is allowed to consume.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SemanticSpatialToken:
    token_id: str
    text: str
    block_type: str  # heading | paragraph | list | table | unknown

    # Geometry mapped directly from M5 BoundingBox
    x: float
    y: float
    width: float
    height: float

    # NORMALIZED PAGE SPACE
    page_width: float
    page_height: float

    # Rendering styling rules mapped from block_type
    font_size: float
    font_weight: int
    alignment: str

    source_region_ids: List[str] = field(default_factory=list)
    reading_order: int = 0
    confidence: float = 0.0
    column_id: int = -1
    spatial_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderablePage:
    page_number: int
    width: float
    height: float
    num_columns: int = 1
    tokens: List[SemanticSpatialToken] = field(default_factory=list)


@dataclass
class RenderableDocument:
    document_id: str
    pages: List[RenderablePage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
