"""
src/pipeline/m5_semantic/contracts.py
Defines the canonical StructuredDocument data model for downstream consumption.
Now includes SpatialGraph as first-class page metadata.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
from src.data_model.document import DocumentMetadata

if TYPE_CHECKING:
    from src.pipeline.m5_semantic.graph.spatial_graph import SpatialGraph


@dataclass(slots=True, frozen=True)
class BoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @classmethod
    def from_tuple(cls, bbox_tuple: tuple[int, int, int, int]) -> "BoundingBox":
        return cls(x_min=bbox_tuple[0], y_min=bbox_tuple[1], x_max=bbox_tuple[2], y_max=bbox_tuple[3])

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.x_min, self.y_min, self.x_max, self.y_max)


@dataclass(slots=True, frozen=True)
class SemanticSpatialToken:
    """
    The canonical unit for the document spatial compiler.
    Binds text and semantic labels strictly to M3 spatial bounding boxes.
    Now produced by the Spatial Graph Engine with graph-resolved reading order.
    """
    token_id: str
    text: str
    block_type: str  # 'paragraph', 'heading', 'list', 'table', 'unknown'
    bbox: BoundingBox
    confidence: float
    reading_order: int
    page_number: int
    source_region_id: str
    column_id: int = -1
    spatial_metadata: dict = field(default_factory=dict)


@dataclass
class StructuredPage:
    """
    A reconstructed page containing ordered semantic spatial tokens
    and the spatial graph that produced the ordering.
    """
    page_number: int
    tokens: list[SemanticSpatialToken]
    page_width: float = 800.0
    page_height: float = 1000.0
    spatial_graph: Any = None  # Optional[SpatialGraph] — kept as Any to avoid circular import


@dataclass(slots=True, frozen=True)
class StructuredDocument:
    """
    The canonical semantic representation of the document.
    Must be the exclusive input for M6 and M8.
    """
    source_document_id: str
    pages: list[StructuredPage]
    metadata: DocumentMetadata
