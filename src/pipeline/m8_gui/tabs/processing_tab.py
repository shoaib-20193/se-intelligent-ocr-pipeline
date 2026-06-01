"""
src/pipeline/m8_gui/tabs/processing_tab.py
Primary runtime interface containing the 4 main panels.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from src.pipeline.m8_gui.components.viewer_canvas import ViewerCanvas
from src.pipeline.m8_gui.components.structure_inspector import StructureInspector
from src.pipeline.m8_gui.components.orchestrator_monitor import OrchestratorMonitor
from src.pipeline.m8_gui.controllers.pipeline_controller import PipelineController

from src.pipeline.m8_gui.components.ingestion_queue import IngestionQueue

class ProcessingTab(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        
        # Horizontal splitter for Left, Center, Right panels
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.left_panel = IngestionQueue()
        self.center_panel = ViewerCanvas()
        self.right_panel = StructureInspector()
        
        h_splitter.addWidget(self.left_panel)
        h_splitter.addWidget(self.center_panel)
        h_splitter.addWidget(self.right_panel)
        h_splitter.setSizes([200, 600, 200])
        
        # Vertical splitter for Top (h_splitter) and Bottom (Orchestrator Monitor)
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(h_splitter)
        
        self.bottom_panel = OrchestratorMonitor()
        v_splitter.addWidget(self.bottom_panel)
        v_splitter.setSizes([600, 200])
        
        main_layout.addWidget(v_splitter)
        
        # Initialize controller bridge
        self.controller = PipelineController(
            viewer=self.center_panel,
            inspector=self.right_panel,
            monitor=self.bottom_panel
        )
        
        # Connect UI triggers to controller
        self.left_panel.start_batch_requested.connect(self._run_pipeline)
        self.left_panel.stop_batch_requested.connect(self.controller.stop_pipeline)
        self.left_panel.files_added.connect(self.controller.update_file_queue)
        
        # Unified export signal: (format, filename, output_dir)
        self.left_panel.export_requested.connect(self.controller.export_document)
        
        # Connect Inspector to Viewer
        self.right_panel.block_selected.connect(self.center_panel.highlight_block)
        
    def _run_pipeline(self):
        self.controller.start_batch()
