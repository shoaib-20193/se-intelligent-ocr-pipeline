"""
PipelineContext — central pipeline state carrier.
Single source of truth for all stage inputs/outputs.
See agents.md §MODULE_CONTRACTS → M7, §EXECUTION_ENGINE
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from src.data_model.request import ProcessingRequest
from src.data_model.document import Document
from src.data_model.preprocessed import PreprocessedDocument
from src.data_model.layout import LayoutDocument
from src.data_model.recognized import RecognizedDocument
from src.data_model.structured import StructuredDocument
from src.data_model.results import ExportSummary
from src.data_model.configs import (
    ProfileConfig, OCRConfig, PostProcessConfig, ExportConfig
)


@dataclass
class PipelineContext:
    """
    Immutable-style carrier — each stage assigns its output to a new field.
    Never mutate fields after assignment; treat each write as a stage checkpoint.

    Usage in M7:
        ctx = PipelineContext(request=req, profile=cfg, ...)
        ctx.document = ingest(ctx.request)
        ctx.preprocessed = preprocess(ctx.document, ctx.profile)
        ...
    """
    # ── Input ────────────────────────────────────────────────────────────────
    request: ProcessingRequest
    profile: ProfileConfig
    ocr_config: OCRConfig
    post_process_config: PostProcessConfig
    export_config: ExportConfig

    # ── M1 output ────────────────────────────────────────────────────────────
    document: Optional[Document] = field(default=None)

    # ── M2 output ────────────────────────────────────────────────────────────
    preprocessed: Optional[PreprocessedDocument] = field(default=None)

    # ── M3 output ────────────────────────────────────────────────────────────
    layout_doc: Optional[LayoutDocument] = field(default=None)

    # ── M4 output ────────────────────────────────────────────────────────────
    recognized_doc: Optional[RecognizedDocument] = field(default=None)

    # ── M5 output ────────────────────────────────────────────────────────────
    structured_doc: Optional[StructuredDocument] = field(default=None)

    # ── M6 output ────────────────────────────────────────────────────────────
    export_summary: Optional[ExportSummary] = field(default=None)

    # ── Internal ─────────────────────────────────────────────────────────────
    pipeline_status: str = "pending"   # "pending"|"running"|"success"|"failed"|"partial"
    error_stage: str = ""
    error_message: str = ""

    def mark_failed(self, stage: str, message: str) -> None:
        self.pipeline_status = "failed"
        self.error_stage = stage
        self.error_message = message

    def mark_success(self) -> None:
        self.pipeline_status = "success"

    @property
    def document_id(self) -> str:
        if self.document:
            return self.document.document_id
        return ""

    @property
    def page_count(self) -> int:
        if self.document:
            return len(self.document.pages)
        return 0
