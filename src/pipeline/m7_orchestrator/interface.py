import os
import uuid
import time
from typing import Dict, Any, Optional

from src.pipeline.m7_orchestrator.runtime.run_context import RunContext
from src.pipeline.m7_orchestrator.runtime.execution_result import PipelineExecutionResult
from src.pipeline.m7_orchestrator.state.state_tracker import StateTracker
from src.pipeline.m7_orchestrator.telemetry.pipeline_metrics import PipelineMetrics
from src.pipeline.m7_orchestrator.debug.pipeline_logger import get_pipeline_logger, OrchestratorEventLogger
from src.pipeline.m7_orchestrator.execution.stage_executor import StageExecutor
from src.pipeline.m7_orchestrator.state.pipeline_state import PipelineState

from concurrent.futures import ThreadPoolExecutor

class M7Orchestrator:
    """
    The central coordinator for the intelligent document processing pipeline.
    """
    def __init__(self, config_flags: Optional[Dict[str, Any]] = None, debug_mode: bool = False):
        self.config_flags = config_flags or {}
        self.debug_mode = debug_mode
        self.logger = get_pipeline_logger()
        self.event_logger = OrchestratorEventLogger(self.logger)
        
        # Shared execution pools for batch concurrency
        self.ocr_pool = ThreadPoolExecutor(max_workers=2)
        self.layout_pool = ThreadPoolExecutor(max_workers=2)
        self.semantic_pool = ThreadPoolExecutor(max_workers=2)
        self.export_pool = ThreadPoolExecutor(max_workers=2)

    def process_document(self, input_path: str) -> PipelineExecutionResult:
        """
        Executes the entire deterministic pipeline for a single document.
        """
        document_id = str(uuid.uuid4())
        
        # 1. Initialize Context
        context = RunContext(
            document_id=document_id,
            input_path=input_path,
            debug_mode=self.debug_mode,
            config_flags=self.config_flags
        )
        
        # 2. Initialize Trackers
        tracker = StateTracker(document_id)
        metrics = PipelineMetrics()
        
        self.event_logger.log_stage_entry("Orchestrator_Init", document_id)
        
        start_time = time.time()
        final_doc = None
        
        try:
            # 3. Execution Loop
            executor = StageExecutor(
                context, tracker, metrics, self.event_logger,
                layout_pool=self.layout_pool,
                ocr_pool=self.ocr_pool,
                semantic_pool=self.semantic_pool,
                export_pool=self.export_pool
            )
            final_doc = executor.execute_pipeline()
            
        except Exception as e:
            # Catches Fatal errors bubbling up
            self.event_logger.log_error(f"Pipeline Terminated: {e}", document_id, is_fatal=True)
            
        finally:
            metrics.total_runtime_s = time.time() - start_time
            
            # 4. Generate Final Result
            result = PipelineExecutionResult(
                document_id=document_id,
                final_state=tracker.current_state,
                structured_document=final_doc,
                metrics=metrics,
                failure_summary=tracker.failure_causes,
                stage_timings=metrics.stage_runtimes_s
            )
            
            self.event_logger.log_summary(document_id, {
                "final_state": result.final_state.name,
                "total_runtime": metrics.total_runtime_s,
                "pages_processed": metrics.total_pages_processed,
                "fatal_failures": metrics.fatal_failures
            })
            
            return result
