"""
M7 — Pipeline Orchestration & Execution Engine [V1 — typed, profile_loader wired]
Stage order M1→M2→M3→M4→M5→M6 IMMUTABLE. M7 does NOT transform data.
See agents.md §MODULE_CONTRACTS → M7, §EXECUTION_ENGINE
"""
from __future__ import annotations
import time
import uuid

from src.data_model.request import ProcessingRequest
from src.data_model.results import PipelineResult
from src.data_model.pipeline_context import PipelineContext
from src.engine.stage_tracker import StageTracker
from src.engine.profile_loader import load_profile
from src.logging.logger import logger

from src.pipeline.m1_ingest.interface import ingest
from src.pipeline.m2_preprocess.interface import preprocess
from src.pipeline.m3_layout.interface import layout_analysis
from src.pipeline.m4_ocr.interface import recognize
from src.pipeline.m5_reconstruct.interface import reconstruct
from src.pipeline.m6_export.interface import export


def run(request: ProcessingRequest) -> PipelineResult:
    """
    M7 single-document pipeline runner.
    All stage I/O passes through PipelineContext — no raw dicts.
    Exception isolation at document boundary per agents.md §ERROR_HANDLING_RULES.
    """
    tracker = StageTracker()
    document_id = str(uuid.uuid4())   # preliminary; replaced by M1's UUID
    wall_start = time.monotonic()

    logger.info(f"Pipeline START — '{request.input_path}'", document_id=document_id)

    try:
        # ── Step 1: Load profile (YAML → typed config objects) ──────────────
        profile, ocr_cfg, pp_cfg, exp_cfg = load_profile(request.profile_id)

        # Build typed PipelineContext (single source of truth)
        ctx = PipelineContext(
            request=request,
            profile=profile,
            ocr_config=ocr_cfg,
            post_process_config=pp_cfg,
            export_config=exp_cfg,
        )
        ctx.pipeline_status = "running"

        # ── Step 2: M1 — Ingest ─────────────────────────────────────────────
        tracker.start("ingest")
        ctx.document = ingest(ctx.request)
        document_id = ctx.document.document_id
        lat = tracker.end("ingest", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "ingest", 0, lat, "ok",
                         f"{ctx.page_count} page(s) — '{ctx.document.metadata.filename}'")

        # ── Step 3: M2 — Preprocess ─────────────────────────────────────────
        tracker.start("preprocess")
        ctx.preprocessed = preprocess(ctx.document, ctx.profile)
        lat = tracker.end("preprocess", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "preprocess", 0, lat, "ok",
                         f"profile={ctx.profile.profile_id}")

        # ── Step 4: M3 — Layout ─────────────────────────────────────────────
        tracker.start("layout")
        ctx.layout_doc = layout_analysis(ctx.preprocessed)
        total_regions = sum(len(p.regions) for p in ctx.layout_doc.pages)
        lat = tracker.end("layout", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "layout", 0, lat, "ok",
                         f"{total_regions} region(s) detected")

        # ── Step 5: M4 — OCR ────────────────────────────────────────────────
        tracker.start("ocr")
        ctx.recognized_doc = recognize(ctx.layout_doc, ctx.ocr_config)
        lat = tracker.end("ocr", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "ocr", 0, lat, "ok",
                         f"device={ctx.ocr_config.device} lang={ctx.ocr_config.language}")

        # ── Step 6: M5 — Reconstruct ────────────────────────────────────────
        tracker.start("reconstruct")
        ctx.structured_doc = reconstruct(ctx.recognized_doc, ctx.post_process_config)
        lat = tracker.end("reconstruct", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "reconstruct", 0, lat, "ok",
                         f"{len(ctx.structured_doc.sections)} section(s), "
                         f"{len(ctx.structured_doc.tables)} table(s)")

        # ── Step 7: M6 — Export ─────────────────────────────────────────────
        tracker.start("export")
        ctx.export_summary = export(ctx.structured_doc, ctx.export_config)
        lat = tracker.end("export", pages_processed=ctx.page_count)
        logger.log_stage(document_id, "export", 0, lat,
                         "ok" if ctx.export_summary.export_status == "success" else "warning",
                         f"status={ctx.export_summary.export_status} "
                         f"files={ctx.export_summary.exported_files}")

        ctx.mark_success()
        total_time = round(time.monotonic() - wall_start, 4)
        logger.info(f"Pipeline COMPLETE in {total_time}s", document_id=document_id)

        return PipelineResult(
            document_id=document_id,
            status="success",
            processing_time=total_time,
            stage_metrics=tracker.to_pipeline_metrics(),
        )

    except Exception as exc:
        total_time = round(time.monotonic() - wall_start, 4)
        logger.log_error(document_id, "M7", 0, type(exc).__name__, str(exc))
        return PipelineResult(
            document_id=document_id,
            status="failed",
            processing_time=total_time,
            stage_metrics=tracker.to_pipeline_metrics(),
        )
