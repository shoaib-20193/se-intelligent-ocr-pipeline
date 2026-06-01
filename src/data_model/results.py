"""PipelineResult, ExportSummary, EvaluationReport — agents.md §DATA_MODEL"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ExportSummary:
    """agents.md §DATA_MODEL → ExportSummary"""
    document_id: str
    exported_files: list[str] = field(default_factory=list)
    export_status: str = "success"    # ENUM: "success"|"partial"|"failed"


@dataclass
class PipelineResult:
    """agents.md §DATA_MODEL → PipelineResult"""
    document_id: str
    status: str = "success"           # ENUM: "success"|"failed"|"partial"
    processing_time: float = 0.0      # total wall-clock seconds
    stage_metrics: dict = field(default_factory=dict)
    # {stage_name: {latency_s: float, pages_processed: int}}


@dataclass
class EvaluationReport:
    """agents.md §DATA_MODEL → EvaluationReport"""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    wer: float = 0.0
    latency_per_page: float = 0.0
    ram_usage_mb: float = 0.0
