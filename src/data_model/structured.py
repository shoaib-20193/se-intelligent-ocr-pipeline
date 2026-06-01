"""StructuredDocument, Section, Table — agents.md §DATA_MODEL → StructuredDocument"""
from __future__ import annotations
from dataclasses import dataclass, field
from src.data_model.document import DocumentMetadata


@dataclass
class Section:
    heading: str    # "" if no heading precedes content
    content: str


@dataclass
class Table:
    rows: list[list[str]] = field(default_factory=list)
    # row-major: rows[row_idx][col_idx]; empty cells = ""


@dataclass
class StructuredDocument:
    metadata: DocumentMetadata
    title: str                              # first "header" region text, or ""
    sections: list[Section] = field(default_factory=list)   # ordered by reading order
    tables: list[Table] = field(default_factory=list)
    raw_text: str = ""                      # concat of all section.content in reading order
