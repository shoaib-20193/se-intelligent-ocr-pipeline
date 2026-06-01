"""
M2 Adapter — Bridges the real M2 bare-function API to M7's unified interface.
Real entrypoint: src.pipeline.m2_preprocess.interface.preprocess(document, profile) -> PreprocessedDocument
"""
from src.data_model.document import Document
from src.data_model.configs import ProfileConfig
from src.data_model.preprocessed import PreprocessedDocument
from src.pipeline.m2_preprocess.interface import preprocess


class M2Adapter:
    """Wraps the real M2 preprocess() bare function as a class with a unified call contract."""

    def execute(self, document: Document, profile: ProfileConfig) -> PreprocessedDocument:
        """
        Translate M7 orchestrator call into the real M2 function call.
        No logic added — pure delegation.
        """
        return preprocess(document, profile)
