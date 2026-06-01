"""
src/pipeline/m8_gui/controllers/pipeline_controller.py
The bridge between M8 UI and the M7 Orchestrator + M6 Export engines.
Runs M7 in a background QThread to prevent UI blocking.
"""
import os
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from src.pipeline.m7_orchestrator.interface import M7Orchestrator
from src.pipeline.m6_export.interface import M6ExportEngine
from src.pipeline.m6_export.contracts import RenderableDocument

def validate_pipeline_contracts():
    """
    Validates that the entire M1 -> M7 pipeline stack is present and importable.
    Fails fast if the architecture is fragmented.
    """
    required_modules = [
        "src.pipeline.m1_ingest",
        "src.pipeline.m2_preprocess",
        "src.pipeline.m3_layout",
        "src.pipeline.m4_ocr",
        "src.pipeline.m5_semantic",
        "src.pipeline.m6_export",
        "src.pipeline.m7_orchestrator"
    ]
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            raise RuntimeError(f"Architecture violation: Missing mandatory pipeline module '{module}'. {e}")

from src.pipeline.m8_gui.events import global_event_bus, PipelineEvent, EventType, CancellationToken, BatchState

# Enforce integration validation before M8 can initialize
validate_pipeline_contracts()

# Format extension map
FORMAT_EXTENSIONS = {
    "json": ".json",
    "txt": ".txt",
    "md": ".md",
    "pdf": ".pdf",
    "docx": ".docx"
}

class PipelineWorker(QObject):
    finished_batch = pyqtSignal()
    finished_doc = pyqtSignal(str, object) # doc_id, RenderableDocument or None
    
    def __init__(self, file_paths: list, cancel_token: CancellationToken):
        super().__init__()
        self.file_paths = file_paths
        self.cancel_token = cancel_token
        
    def run(self):
        orchestrator = M7Orchestrator()
        
        # M6 export operations will run in orchestrator's export pool
        
        futures = []
        for file_path in self.file_paths:
            if self.cancel_token.is_cancelled():
                global_event_bus.emit_event(PipelineEvent(
                    document_id="BATCH", event_type=EventType.ERROR, stage_name="CANCEL",
                    progress=1.0, message="Batch execution cancelled by user."
                ))
                break
                
            futures.append(orchestrator.export_pool.submit(self._process_single_document, orchestrator, file_path))
            
        # Wait for all futures to complete
        for future in futures:
            future.result()
            
        self.finished_batch.emit()
        
    def _process_single_document(self, orchestrator, file_path: str):
        if self.cancel_token.is_cancelled():
            return
            
        global_event_bus.emit_event(PipelineEvent(
            document_id=file_path, event_type=EventType.STAGE, stage_name="M1_Ingest",
            progress=0.1, message=f"Starting processing: {file_path}"
        ))
        
        try:
            result = orchestrator.process_document(file_path)
            
            if result.structured_document:
                global_event_bus.emit_event(PipelineEvent(
                    document_id=file_path, event_type=EventType.STAGE, stage_name="M6_Export",
                    progress=0.9, message="Compiling RenderableDocument..."
                ))
                
                # We can just run the M6 to_renderable synchronously here as it is very fast
                renderable_doc = M6ExportEngine.to_renderable(result.structured_document)
                
                global_event_bus.emit_event(PipelineEvent(
                    document_id=file_path, event_type=EventType.COMPLETE, stage_name="Done",
                    progress=1.0, message="Processing complete."
                ))
                self.finished_doc.emit(file_path, renderable_doc)
            else:
                global_event_bus.emit_event(PipelineEvent(
                    document_id=file_path, event_type=EventType.ERROR, stage_name="M7_Orchestrator",
                    progress=1.0, message="Failed to produce StructuredDocument."
                ))
                self.finished_doc.emit(file_path, None)
                
        except Exception as e:
            global_event_bus.emit_event(PipelineEvent(
                document_id=file_path, event_type=EventType.ERROR, stage_name="FATAL",
                progress=1.0, message=str(e)
            ))
            self.finished_doc.emit(file_path, None)


class PipelineController(QObject):
    def __init__(self, viewer, inspector, monitor):
        super().__init__()
        self.viewer = viewer
        self.inspector = inspector
        self.monitor = monitor
        
        self.current_renderable_doc = None
        self.worker = None
        self.thread = None
        self.cancel_token = None
        
        
        self.file_queue = []
        self.processed_count = 0
        
        global_event_bus.event_emitted.connect(self._handle_pipeline_event)
        
    def update_file_queue(self, paths: list):
        self.file_queue = paths

    def start_batch(self):
        if not self.file_queue:
            self.monitor.append_log("No files in queue to process.")
            return
            
        self.processed_count = 0
        self.monitor.update_batch_progress(self.processed_count, len(self.file_queue))
        self.monitor.append_log(f"--- Starting Batch Execution: {len(self.file_queue)} files ---")
        
        self.cancel_token = CancellationToken()
        self.thread = QThread()
        self.worker = PipelineWorker(self.file_queue.copy(), self.cancel_token)
        
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        
        self.worker.finished_doc.connect(self._on_doc_finished)
        self.worker.finished_batch.connect(self._on_batch_finished)
        
        self.thread.start()
        
    def stop_pipeline(self):
        if self.cancel_token and self.thread and self.thread.isRunning():
            self.monitor.append_log("Cancellation requested. Waiting for safe interruption...")
            self.cancel_token.cancel()
        else:
            self.monitor.append_log("No pipeline is currently running.")

    def _on_doc_finished(self, file_path: str, renderable_doc: RenderableDocument):
        self.processed_count += 1
        self.monitor.update_batch_progress(self.processed_count, len(self.file_queue))
        
        if renderable_doc:
            self.current_renderable_doc = renderable_doc
            self.viewer.load_renderable_document(renderable_doc)
            self.inspector.load_renderable_document(renderable_doc)
            
    def _on_batch_finished(self):
        self.monitor.append_log("--- Batch Execution Finished ---")
        self.thread.quit()
        self.thread.wait()
        
    def _handle_pipeline_event(self, event: PipelineEvent):
        # Update monitor
        time_str = event.timestamp.strftime("%H:%M:%S")
        self.monitor.append_log(f"[{time_str}] [{event.stage_name}] {event.document_id}: {event.message}")

    def export_document(self, fmt: str, filename: str, output_dir: str):
        """
        Unified export dispatcher. Routes to the correct M6 exporter based on format.
        
        Args:
            fmt: One of 'json', 'txt', 'md', 'pdf', 'docx'
            filename: Base filename (without extension)
            output_dir: Directory to write the file into
        """
        if not self.current_renderable_doc:
            self.monitor.append_log("Export failed: No document has been processed yet.")
            return
            
        ext = FORMAT_EXTENSIONS.get(fmt, ".json")
        full_path = os.path.join(output_dir, f"{filename}{ext}")
        
        export_map = {
            "json": M6ExportEngine.export_json,
            "txt": M6ExportEngine.export_txt,
            "md": M6ExportEngine.export_md,
            "pdf": M6ExportEngine.export_pdf,
            "docx": M6ExportEngine.export_docx
        }
        
        exporter = export_map.get(fmt)
        if not exporter:
            self.monitor.append_log(f"Export failed: Unknown format '{fmt}'")
            return
            
        try:
            actual_path = exporter(self.current_renderable_doc, full_path)
            self.monitor.append_log(f"Successfully exported {fmt.upper()} via M6 to: {actual_path}")
        except Exception as e:
            self.monitor.append_log(f"{fmt.upper()} Export failed: {e}")
