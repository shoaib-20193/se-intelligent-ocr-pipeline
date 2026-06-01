"""
M1 Adapter — Bridges the real M1 bare-function API to M7's unified interface.
Real entrypoint: src.pipeline.m1_ingest.interface.ingest(request) -> Document
"""
from src.data_model.request import ProcessingRequest
from src.data_model.document import Document
from src.pipeline.m1_ingest.interface import ingest


class M1Adapter:
    """Wraps the real M1 bare function as a class with a unified call contract."""

    def execute(self, request: ProcessingRequest) -> Document:
        """
        Translate M7 orchestrator call into the real M1 function call.
        No logic added — pure delegation.
        """
        return ingest(request)
