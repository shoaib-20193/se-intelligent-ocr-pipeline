"""Document, RawPage — agents.md §DATA_MODEL → Document, RawPage"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentMetadata:
    filename: str
    file_size: int            # bytes
    page_count: int
    resolution: tuple[int, int]  # (width_px, height_px) of first page

    def copy(self):
        return DocumentMetadata(
            **self.__dict__.copy()
        )


@dataclass
class RawPage:
    page_number: int          # 1-indexed
    image: Any = None         # np.ndarray in real impl; None placeholder in V0


@dataclass
class Document:
    document_id: str          # UUID
    metadata: DocumentMetadata
    pages: list[RawPage] = field(default_factory=list)
