"""
src/pipeline/m5_semantic/interface.py
Public entrypoint for the M5 Semantic Reconstruction module.
"""
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m5_semantic.contracts import StructuredDocument
from src.pipeline.m5_semantic.reconstructor import SemanticReconstructor

class M5SemanticReconstructor:
    """
    Adapter interface for orchestration.
    """
    
    def __init__(self):
        self._reconstructor = SemanticReconstructor()
        
    def execute(self, document: RecognizedDocument) -> StructuredDocument:
        """
        Executes the semantic reconstruction phase.
        Converts M4 OCR output into the canonical StructuredDocument model.
        """
        return self._reconstructor.reconstruct(document)
