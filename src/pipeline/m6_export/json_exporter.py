"""
json_exporter — serialize StructuredDocument to JSON.
See agents.md §MODULE_CONTRACTS → M6 → Format: JSON
"""
from __future__ import annotations
import json
from src.data_model.structured import StructuredDocument


def _metadata_to_dict(meta) -> dict:
    return {
        "filename": meta.filename,
        "file_size": meta.file_size,
        "page_count": meta.page_count,
        "resolution": list(meta.resolution),
    }


def serialize(doc: StructuredDocument) -> str:
    """
    Serialize StructuredDocument to a deterministic JSON string.
    Image arrays (np.ndarray) are excluded — text/structure only.
    Returns: UTF-8 JSON string
    """
    payload = {
        "title": doc.title,
        "metadata": _metadata_to_dict(doc.metadata),
        "sections": [
            {"heading": s.heading, "content": s.content}
            for s in doc.sections
        ],
        "tables": [
            {"rows": table.rows}
            for table in doc.tables
        ],
        "raw_text": doc.raw_text,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
