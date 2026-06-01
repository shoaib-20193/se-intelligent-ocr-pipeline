"""
src/pipeline/m7_orchestrator/execution/stage_executor.py
Sequentially executes M1 → M2 → M3 → M4 via adapter bindings to real modules.
No concurrency. No async. Deterministic execution only.
"""
import time
import logging

from src.pipeline.m7_orchestrator.runtime.run_context import RunContext
from src.pipeline.m7_orchestrator.state.pipeline_state import PipelineState
from src.pipeline.m7_orchestrator.state.state_tracker import StateTracker
from src.pipeline.m7_orchestrator.telemetry.pipeline_metrics import PipelineMetrics
from src.pipeline.m7_orchestrator.debug.pipeline_logger import OrchestratorEventLogger
from src.pipeline.m7_orchestrator.errors.pipeline_exceptions import FatalPipelineError
from src.pipeline.m7_orchestrator.errors.recovery_manager import RecoveryManager, RecoveryPolicyAction
from src.pipeline.m7_orchestrator.contracts.stage_contracts import StageIOValidator

# Adapter imports — these bind to the REAL M1-M4 implementations
from src.pipeline.m7_orchestrator.adapters.m1_adapter import M1Adapter
from src.pipeline.m7_orchestrator.adapters.m2_adapter import M2Adapter
from src.pipeline.m7_orchestrator.adapters.m3_adapter import M3Adapter
from src.pipeline.m7_orchestrator.adapters.m4_adapter import M4Adapter
from src.pipeline.m7_orchestrator.adapters.m5_adapter import M5Adapter

from src.data_model.request import ProcessingRequest, InputConstraints
from src.data_model.configs import ProfileConfig
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m5_semantic.contracts import StructuredDocument

logger = logging.getLogger(__name__)


class StageExecutor:
    """
    Executes M1 -> M2 -> M3 -> M4 sequentially and deterministically.
    All stage calls go through thin adapter wrappers around the real module code.
    """
    def __init__(self, context: RunContext, tracker: StateTracker,
                 metrics: PipelineMetrics, event_logger: OrchestratorEventLogger,
                 layout_pool=None, ocr_pool=None, semantic_pool=None, export_pool=None):
        self.context = context
        self.tracker = tracker
        self.metrics = metrics
        self.event_logger = event_logger
        self.layout_pool = layout_pool
        self.ocr_pool = ocr_pool
        self.semantic_pool = semantic_pool
        self.export_pool = export_pool

        # Instantiate adapters (thin wrappers around real implementations)
        self.m1 = M1Adapter()
        self.m2 = M2Adapter()
        self.m3 = M3Adapter(debug_viz=context.debug_mode)
        self.m4 = M4Adapter(confidence_threshold=context.get_flag("confidence_threshold", 0.5))
        self.m5 = M5Adapter()

        self.validator = StageIOValidator()

    def resolve_final_state(self, metrics: PipelineMetrics, structured_document: StructuredDocument | None, fatal_error: bool) -> PipelineState:
        """
        Reconciles the final pipeline state based on actual outputs and metrics,
        not just execution path completion.
        Final state depends ONLY on final execution outcome, not historical errors.
        """
        if fatal_error:
            return PipelineState.FAILED
            
        if structured_document is None:
            return PipelineState.PARTIAL_FAILURE
        
        # Successful execution even if OCR output is empty
        return PipelineState.COMPLETED

    def execute_pipeline(self):
        """
        Runs the fully orchestrated pipeline. Returns the final RecognizedDocument
        on success. Raises FatalPipelineError on unrecoverable failure.
        """
        doc_id = self.context.document_id

        try:
            # --- Build ProcessingRequest from RunContext ---
            request = ProcessingRequest(
                input_path=self.context.input_path,
                profile_id=self.context.get_flag("profile_id", "fast_draft"),
                output_formats=self.context.get_flag("formats", ["json"]),
                constraints=InputConstraints(
                    max_pages=self.context.get_flag("max_pages", 100),
                    max_file_size_mb=self.context.get_flag("max_file_size_mb", 50),
                ),
            )

            # ───────── M1 INGEST ─────────
            self._log_stage_entry("M1_Ingest")
            t0 = time.time()
            document = self.m1.execute(request)
            document = self.validator.validate_m1_output(document)
            self._log_stage_exit("M1_Ingest", time.time() - t0)
            self.tracker.transition_to(PipelineState.LOADED)

            # ───────── M2 PREPROCESS ─────────
            self._log_stage_entry("M2_Preprocess")
            t0 = time.time()
            profile = ProfileConfig(
                profile_id=self.context.get_flag("profile_id", "fast_draft"),
            )
            preprocessed_doc = self.m2.execute(document, profile)
            preprocessed_doc = self.validator.validate_m2_output(preprocessed_doc)
            self._log_stage_exit("M2_Preprocess", time.time() - t0)
            self.tracker.transition_to(PipelineState.PREPROCESSED)

            # Stash clean images for M4 (M4 needs page_number → ndarray map)
            clean_images = {
                p.page_number: p.clean_image
                for p in preprocessed_doc.pages
                if p.clean_image is not None
            }

            # ───────── M3 LAYOUT ─────────
            self._log_stage_entry("M3_Layout")
            t0 = time.time()
            if self.layout_pool:
                layout_future = self.layout_pool.submit(self.m3.execute, preprocessed_doc)
                layout_doc = layout_future.result()
            else:
                layout_doc = self.m3.execute(preprocessed_doc)
                
            layout_doc = self.validator.validate_m3_output(layout_doc)
            self._log_stage_exit("M3_Layout", time.time() - t0)
            self.tracker.transition_to(PipelineState.LAYOUT_ANALYZED)

            # ───────── M4 OCR ─────────
            self._log_stage_entry("M4_OCR")
            t0 = time.time()

            def _run_m4():
                return self.m4.execute(layout_doc, clean_images)

            if self.ocr_pool:
                ocr_future = self.ocr_pool.submit(RecoveryManager.execute_with_retry, _run_m4, max_retries=2)
                recognized_doc = ocr_future.result()
            else:
                recognized_doc = RecoveryManager.execute_with_retry(_run_m4, max_retries=2)
                
            recognized_doc = self.validator.validate_m4_output(recognized_doc)
            self._log_stage_exit("M4_OCR", time.time() - t0)
            self.tracker.transition_to(PipelineState.OCR_COMPLETED)

            # Update metrics
            self.metrics.total_pages_processed = len(recognized_doc.pages)
            self.metrics.total_regions_processed = sum(
                len(p.regions) for p in recognized_doc.pages
            )

            # ───────── M5 SEMANTIC RECONSTRUCTION ─────────
            self._log_stage_entry("M5_Semantic")
            t0 = time.time()
            
            enable_m5 = self.context.get_flag("ENABLE_M5_SEMANTIC_LAYER", True)
            
            def _run_m5():
                if enable_m5:
                    return self.m5.execute(recognized_doc)
                else:
                    logger.info("M5 semantic layer bypassed via feature flag. Using fallback structure.")
                    return self.m5._execute_fallback(recognized_doc)
                    
            try:
                if self.semantic_pool:
                    m5_future = self.semantic_pool.submit(_run_m5)
                    structured_doc = m5_future.result()
                else:
                    structured_doc = _run_m5()
                    
                structured_doc = self.validator.validate_m5_output(structured_doc)
                self._log_stage_exit("M5_Semantic", time.time() - t0)
                self.tracker.transition_to(PipelineState.M5_SEMANTIC_RECONSTRUCTION)
            except Exception as e:
                logger.error(f"M5 execution failed fatally: {e}")
                self.tracker.transition_to(PipelineState.M5_FAILURE, failure_cause=str(e))
                # Fallback to empty if absolutely everything fails
                structured_doc = None

            # ───────── SUCCESS / RECONCILIATION ─────────
            # Explicit success flag independent of any recovery events
            self._pipeline_successfully_completed = True
            
            final_state = self.resolve_final_state(self.metrics, structured_doc, fatal_error=False)
            self.tracker.transition_to(final_state)
            
            if final_state == PipelineState.PARTIAL_FAILURE:
                self.event_logger.log_error(
                    "Pipeline completed execution but output is empty or recovery events occurred.",
                    doc_id, is_fatal=False
                )
            elif final_state == PipelineState.COMPLETED and structured_doc:
                total_regions = sum(len(p.tokens) for p in structured_doc.pages)
                if total_regions == 0:
                    logger.warning("Empty output (valid execution)")
            
            return structured_doc

        except Exception as e:
            self._pipeline_successfully_completed = False
            policy = RecoveryManager.handle_error(e, context="Pipeline Execution")
            
            # IF fatal_error_occurred: return FAILED
            if policy == RecoveryPolicyAction.FAIL_FAST:
                self.tracker.transition_to(PipelineState.FAILED, failure_cause=str(e))
                self.event_logger.log_error(
                    f"Pipeline halted on fatal error: {e}", doc_id, is_fatal=True
                )
                self.metrics.add_fatal_failure()
                raise FatalPipelineError(
                    f"Pipeline failed at state {self.tracker.current_state.name}: {e}"
                ) from e
            
            # ELSE: return PARTIAL_FAILURE
            else:
                self.tracker.transition_to(
                    PipelineState.PARTIAL_FAILURE, failure_cause=str(e)
                )
                self.event_logger.log_error(
                    f"Pipeline completing with partial failure: {e}",
                    doc_id, is_fatal=False,
                )
                self.metrics.add_recoverable_failure()
                return None  # best-effort; caller builds result from tracker state

    # ── helpers ──
    def _log_stage_entry(self, stage: str):
        self.event_logger.log_stage_entry(stage, self.context.document_id)

    def _log_stage_exit(self, stage: str, duration: float):
        self.metrics.record_stage_time(stage, duration)
        self.event_logger.log_stage_exit(stage, self.context.document_id, duration)
