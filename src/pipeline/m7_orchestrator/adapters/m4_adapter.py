"""
M4 Adapter — Bridges the real M4 class API to M7's unified interface.
Real entrypoint: src.pipeline.m4_ocr.interface.M4OCREngine.recognize_document(layout_doc, clean_images) -> RecognizedDocument
"""

from src.data_model.layout import LayoutDocument
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m4_ocr.interface import M4OCREngine

# Strict runtime config for M4 OCR
from src.pipeline.m7_orchestrator.contracts.runtime_config import M4RuntimeConfig

import logging

from src.pipeline.m4_ocr.contracts.ocr_runtime_contracts import LegacyPaddleConfig

class M4Adapter:
    """Wraps the real M4OCREngine class for M7 consumption.
    Configuration is provided via M4RuntimeConfig mapped to LegacyPaddleConfig.
    """

    def __init__(self, confidence_threshold: float = 0.5):
        self._runtime_config = M4RuntimeConfig()
        
        init_config = LegacyPaddleConfig(
            device=self._runtime_config.resolve_device(),
            enable_mkldnn=self._runtime_config.enable_mkldnn
        )
        
        self._engine = M4OCREngine(
            confidence_threshold=confidence_threshold, 
            init_config=init_config
        )
        self._logger = logging.getLogger(__name__)

    def execute(self, layout_doc: LayoutDocument, clean_images: dict) -> RecognizedDocument:
        """Execute OCR without passing runtime kwargs. Clean images are directly provided."""
        return self._engine.recognize_document(layout_doc, clean_images)
