"""
tests/orchestrator/test_m7_pipeline.py
Integration tests for the M7 Orchestrator using adapter-bound real modules.
All stage logic is mocked at the ADAPTER layer to keep tests fast and deterministic.
"""
import pytest
import os
import json
import sys

from src.pipeline.m7_orchestrator.interface import M7Orchestrator
from src.pipeline.m7_orchestrator.state.pipeline_state import PipelineState
from src.pipeline.m7_orchestrator.errors.pipeline_exceptions import FatalPipelineError, ContractViolationError
from src.pipeline.m7_orchestrator.runtime.execution_result import PipelineExecutionResult
from src.pipeline.m7_orchestrator.telemetry.pipeline_metrics import PipelineMetrics

from src.data_model.request import ProcessingRequest
from src.data_model.document import Document, DocumentMetadata
from src.data_model.preprocessed import PreprocessedDocument, ProcessedPage
from src.data_model.layout import LayoutDocument
from src.data_model.ocr import RecognizedDocument

import numpy as np


# ── Shared mock data ──────────────────────────────────────────────────────────

_MOCK_META = DocumentMetadata("test.pdf", 100, 1, (100, 100))
_MOCK_IMAGE = np.ones((100, 100, 3), dtype=np.uint8) * 255


@pytest.fixture
def mock_adapters(monkeypatch):
    """
    Mocks all four adapter .execute() methods to return valid minimal DTOs.
    This keeps tests independent of heavy model loading (DocTR, PaddleOCR).
    """
    def mock_m1(self, req):
        from src.data_model.document import RawPage
        return Document("doc1", _MOCK_META, [RawPage(page_number=1, image=_MOCK_IMAGE)])

    def mock_m2(self, doc, config):
        return PreprocessedDocument(_MOCK_META, [ProcessedPage(page_number=1, clean_image=_MOCK_IMAGE)])

    def mock_m3(self, doc):
        return LayoutDocument("doc1", _MOCK_META, [])

    def mock_m4(self, doc, clean_imgs):
        from src.data_model.ocr import RecognizedPage, RecognizedRegion
        dummy_region = RecognizedRegion("p1-r1", (0,0,10,10), "text", 0.9, "r1", 1, None)
        dummy_page = RecognizedPage(1, [dummy_region], "text")
        return RecognizedDocument("doc1", [dummy_page], _MOCK_META)

    monkeypatch.setattr("src.pipeline.m7_orchestrator.adapters.m1_adapter.M1Adapter.execute", mock_m1)
    monkeypatch.setattr("src.pipeline.m7_orchestrator.adapters.m2_adapter.M2Adapter.execute", mock_m2)
    monkeypatch.setattr("src.pipeline.m7_orchestrator.adapters.m3_adapter.M3Adapter.execute", mock_m3)
    monkeypatch.setattr("src.pipeline.m7_orchestrator.adapters.m4_adapter.M4Adapter.execute", mock_m4)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_m7_deterministic_success(mock_adapters):
    """Happy path: M1 → M2 → M3 → M4 succeed, final state is COMPLETED."""
    orchestrator = M7Orchestrator()
    result = orchestrator.process_document("dummy.pdf")

    assert result.final_state == PipelineState.COMPLETED
    assert result.metrics.fatal_failures == 0
    assert "M1_Ingest" in result.stage_timings
    assert "M2_Preprocess" in result.stage_timings
    assert "M3_Layout" in result.stage_timings
    assert "M4_OCR" in result.stage_timings


def test_contract_violation_blocking(mock_adapters, monkeypatch):
    """M2 returning a bad DTO must trigger FAIL_FAST."""
    def mock_bad_m2(self, doc, config):
        return "BAD_DTO_STRING"

    monkeypatch.setattr(
        "src.pipeline.m7_orchestrator.adapters.m2_adapter.M2Adapter.execute",
        mock_bad_m2,
    )

    orchestrator = M7Orchestrator()
    result = orchestrator.process_document("dummy.pdf")

    assert result.final_state == PipelineState.FAILED
    assert result.metrics.fatal_failures == 1
    assert any("Contract Violation" in err for err in result.failure_summary)


def test_recovery_policy_retry(mock_adapters, monkeypatch):
    """Transient M4 error on first call should succeed on retry."""
    call_count = {"n": 0}

    def mock_flaky_m4(self, doc, clean_imgs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Transient PaddleOCR init error")
        from src.data_model.ocr import RecognizedPage, RecognizedRegion
        dummy_region = RecognizedRegion("p1-r1", (0,0,10,10), "text", 0.9, "r1", 1, None)
        dummy_page = RecognizedPage(1, [dummy_region], "text")
        return RecognizedDocument("doc1", [dummy_page], _MOCK_META)

    monkeypatch.setattr(
        "src.pipeline.m7_orchestrator.adapters.m4_adapter.M4Adapter.execute",
        mock_flaky_m4,
    )

    orchestrator = M7Orchestrator()
    result = orchestrator.process_document("dummy.pdf")

    assert call_count["n"] == 2
    assert result.final_state == PipelineState.COMPLETED


def test_jsonl_log_generation(mock_adapters, tmp_path, monkeypatch):
    """Verify pipeline emits valid JSONL log entries."""
    log_file = str(tmp_path / "test.jsonl")

    import src.pipeline.m7_orchestrator.debug.pipeline_logger as pl_mod

    def mock_get_logger(*a, **kw):
        return pl_mod.get_pipeline_logger(
            name="test_logger", log_file=log_file, console_human_readable=False
        )

    monkeypatch.setattr(
        "src.pipeline.m7_orchestrator.interface.get_pipeline_logger",
        mock_get_logger,
    )

    orchestrator = M7Orchestrator()
    orchestrator.process_document("dummy.pdf")

    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) > 0
    log_obj = json.loads(lines[0])
    assert "timestamp" in log_obj
    assert "level" in log_obj
    assert "message" in log_obj
    assert "pipeline_data" in log_obj


def test_cli_entry_point_execution(monkeypatch, capsys):
    """CLI must call process_document and exit 0 on success."""
    def mock_process(self, input_path):
        return PipelineExecutionResult(
            document_id="cli_test",
            final_state=PipelineState.COMPLETED,
            recognized_document=None,
            metrics=PipelineMetrics(total_runtime_s=1.0),
        )

    monkeypatch.setattr(
        "src.pipeline.m7_orchestrator.interface.M7Orchestrator.process_document",
        mock_process,
    )
    monkeypatch.setattr(sys, "argv", ["run.py", "--input", "test.pdf"])

    class ExitException(Exception):
        pass

    monkeypatch.setattr(sys, "exit", lambda x: (_ for _ in ()).throw(ExitException(x)))

    from src.pipeline.m7_orchestrator.run import main

    try:
        main()
    except ExitException as e:
        assert e.args[0] == 0

    captured = capsys.readouterr()
    assert "Success! Recognized Document Generated." in captured.out


def test_state_transition_validity():
    """Illegal state jump must raise ValueError."""
    from src.pipeline.m7_orchestrator.state.state_tracker import StateTracker

    tracker = StateTracker("test_doc")
    # INITIALIZED -> OCR_COMPLETED is illegal (must go through LOADED first)
    with pytest.raises(ValueError, match="Illegal pipeline state transition"):
        tracker.transition_to(PipelineState.OCR_COMPLETED)
