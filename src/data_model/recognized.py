"""RecognizedDocument, RecognizedPage, RecognizedRegion — agents.md §DATA_MODEL"""
from __future__ import annotations
from dataclasses import dataclass, field
from src.data_model.document import DocumentMetadata


@dataclass
class RecognizedRegion:
    region_id: str
    type: str
    bbox: tuple[int, int, int, int]
    text: str                    # raw OCR output string
    ocr_confidence: float        # [0.0, 1.0]
    layout_confidence: float     # inherited from Region.confidence


@dataclass
class RecognizedPage:
    page_number: int
    regions: list[RecognizedRegion] = field(default_factory=list)


@dataclass
class RecognizedDocument:
    metadata: DocumentMetadata
    pages: list[RecognizedPage] = field(default_factory=list)
