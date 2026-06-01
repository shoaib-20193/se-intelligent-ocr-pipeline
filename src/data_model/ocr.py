"""
src/data_model/ocr.py
V4 OCR Awakening DTOs.
Strictly defines immutable data structures for M4 outputs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from src.data_model.document import DocumentMetadata


@dataclass(slots=True, frozen=True)
class RecognizedRegion:
    """
    A single text region successfully processed by OCR.
    Inherits geometry and spatial metadata directly from M3 Layout Region.
    Adds text content and recognition confidence.
    """
    id: str
    bbox: tuple[int, int, int, int]
    text: str
    confidence: float
    source_region_id: str
    reading_order: int
    crop_ref: dict | None  # Optional ref inherited from M3
    spatial_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RecognizedPage:
    """
    A single page of recognized regions, ordered strictly by reading_order.
    """
    page_number: int
    regions: list[RecognizedRegion]
    raw_text: str  # Concatenated text from all regions in reading_order
    page_width: int = 800
    page_height: int = 1000


@dataclass(slots=True, frozen=True)
class RecognizedDocument:
    """
    Final output of M4 OCR Engine.
    """
    source_document_id: str
    pages: list[RecognizedPage]
    metadata: DocumentMetadata
