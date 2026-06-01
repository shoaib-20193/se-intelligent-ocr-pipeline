"""
LayoutDocument, LayoutPage, Region — M3 output data contracts.
agents.md §DATA_MODEL → LayoutDocument
Strictly spatial/geometric. Semantics forbidden.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from src.data_model.document import DocumentMetadata

@dataclass(frozen=True)
class Region:
    """
    A single detected layout region within a page.
    Strictly spatial/geometric. Semantics forbidden.
    """
    id: str                                     # format: "p{page}-r{idx}"
    bbox: tuple[int, int, int, int]             # (x1, y1, x2, y2) integer pixel coords
    polygon: Optional[list[tuple[int, int]]]    # list of (x,y) from DocTR
    confidence: float                           # [0.0, 1.0]
    type: str = "text_block"                    # strictly "text_block" in M3
    spatial_metadata: dict = field(default_factory=dict) # cluster_id, reading_order, etc.
    crop_ref: Optional[dict] = None             # {"page_id": str, "bbox": [x1,y1,x2,y2]}

    @property
    def x1(self) -> int: return self.bbox[0]
    @property
    def y1(self) -> int: return self.bbox[1]
    @property
    def x2(self) -> int: return self.bbox[2]
    @property
    def y2(self) -> int: return self.bbox[3]
    @property
    def width(self) -> int: return self.bbox[2] - self.bbox[0]
    @property
    def height(self) -> int: return self.bbox[3] - self.bbox[1]
    @property
    def area(self) -> int: return self.width * self.height
    @property
    def center_x(self) -> float: return (self.bbox[0] + self.bbox[2]) / 2.0
    @property
    def center_y(self) -> float: return (self.bbox[1] + self.bbox[3]) / 2.0


@dataclass
class LayoutPage:
    """
    Detected layout for a single document page.
    """
    page_number: int
    regions: list[Region] = field(default_factory=list)  # ordered by reading order
    layout_type: str = "unknown"
    column_count: int = 1
    metadata: dict = field(default_factory=dict)


@dataclass
class LayoutDocument:
    """
    Full layout-aware document representation produced by M3.
    """
    document_id: str
    metadata: DocumentMetadata
    pages: list[LayoutPage] = field(default_factory=list)
    processing_metadata: dict = field(default_factory=dict)
