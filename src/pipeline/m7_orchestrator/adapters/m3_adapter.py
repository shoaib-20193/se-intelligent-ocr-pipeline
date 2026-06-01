"""
M3 Adapter — Bridges the real M3 class API to M7's unified interface.
Real entrypoint: src.pipeline.m3_layout.interface.M3LayoutEngine.layout_analysis(preprocessed_doc) -> LayoutDocument
"""
from src.data_model.preprocessed import PreprocessedDocument
from src.data_model.layout import LayoutDocument
from src.pipeline.m3_layout.interface import M3LayoutEngine


class M3Adapter:
    """Wraps the real M3LayoutEngine class for M7 consumption."""

    def __init__(self, debug_viz: bool = False):
        self._engine = M3LayoutEngine(backend_name="doctr", debug_viz=debug_viz)

    def execute(self, preprocessed_doc: PreprocessedDocument) -> LayoutDocument:
        """
        Translate M7 orchestrator call into the real M3 class method.
        No logic added — pure delegation.
        """
        return self._engine.layout_analysis(preprocessed_doc)
