"""LogEntry schema — agents.md §EXECUTION_ENGINE → Stage Logging"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LogEntry:
    timestamp: str         # ISO-8601
    document_id: str
    stage: str             # "ingest"|"preprocess"|"layout"|"ocr"|"reconstruct"|"export"
    page_number: int
    latency_s: float
    status: str            # "ok"|"warning"|"error"
    message: str
