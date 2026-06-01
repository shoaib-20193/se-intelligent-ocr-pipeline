"""
M6 schema_validator — validates StructuredDocument before any write.
Mandatory — never skipped. See agents.md §MODULE_CONTRACTS → M6
"""
from __future__ import annotations
from src.data_model.structured import StructuredDocument


class SchemaValidationError(Exception):
    """Raised when StructuredDocument fails pre-write validation."""


def validate(doc: StructuredDocument) -> None:
    """
    Validate StructuredDocument schema completeness.
    Raises SchemaValidationError on any violation.
    """
    if not isinstance(doc.title, str):
        raise SchemaValidationError(f"title must be str, got {type(doc.title)}")

    if not isinstance(doc.raw_text, str):
        raise SchemaValidationError(f"raw_text must be str, got {type(doc.raw_text)}")

    if not isinstance(doc.sections, list):
        raise SchemaValidationError("sections must be a list")

    if not isinstance(doc.tables, list):
        raise SchemaValidationError("tables must be a list")

    for i, section in enumerate(doc.sections):
        if not isinstance(section.heading, str):
            raise SchemaValidationError(f"sections[{i}].heading must be str")
        if not isinstance(section.content, str):
            raise SchemaValidationError(f"sections[{i}].content must be str")

    for i, table in enumerate(doc.tables):
        if not isinstance(table.rows, list):
            raise SchemaValidationError(f"tables[{i}].rows must be a list")
        for j, row in enumerate(table.rows):
            if not isinstance(row, list):
                raise SchemaValidationError(f"tables[{i}].rows[{j}] must be a list")
            for k, cell in enumerate(row):
                if not isinstance(cell, str):
                    raise SchemaValidationError(
                        f"tables[{i}].rows[{j}][{k}] must be str, got {type(cell)}"
                    )

    # Metadata checks
    meta = doc.metadata
    if not hasattr(meta, "filename") or not isinstance(meta.filename, str):
        raise SchemaValidationError("metadata.filename must be str")
    if not hasattr(meta, "page_count") or not isinstance(meta.page_count, int):
        raise SchemaValidationError("metadata.page_count must be int")
