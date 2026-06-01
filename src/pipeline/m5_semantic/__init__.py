"""
src/pipeline/m5_semantic/__init__.py
M5 Semantic Reconstruction module.
Powered by the Spatial Graph Engine — converts flat M3/M4 output into
a structured document topology with correct reading order and column awareness.
"""
from src.pipeline.m5_semantic.interface import M5SemanticReconstructor
from src.pipeline.m5_semantic.contracts import (
    StructuredDocument,
    StructuredPage,
    SemanticSpatialToken,
    BoundingBox
)

__all__ = [
    "M5SemanticReconstructor",
    "StructuredDocument",
    "StructuredPage",
    "SemanticSpatialToken",
    "BoundingBox"
]
