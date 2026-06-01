"""
src/pipeline/m7_orchestrator/adapters/m5_adapter.py
Adapter for M5 Semantic Reconstruction module.
Includes non-fatal fallback behavior as per M7 contracts.
"""
import logging
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m5_semantic.contracts import StructuredDocument, StructuredPage, SemanticSpatialToken, BoundingBox
from src.pipeline.m5_semantic.interface import M5SemanticReconstructor

logger = logging.getLogger(__name__)

class M5Adapter:
    def __init__(self):
        self.reconstructor = M5SemanticReconstructor()

    def execute(self, document: RecognizedDocument) -> StructuredDocument:
        """
        Executes M5 semantic reconstruction via Spatial Graph Engine.
        If it fails, falls back to a minimal wrapper that preserves OCR bounding boxes.
        """
        try:
            return self.reconstructor.execute(document)
        except Exception as e:
            logger.error(f"[M5_ADAPTER] Spatial Graph Engine failed: {e}. Executing non-fatal fallback.")
            return self._execute_fallback(document)

    def _execute_fallback(self, document: RecognizedDocument) -> StructuredDocument:
        """
        Creates a minimal StructuredDocument directly from RecognizedDocument
        without the Spatial Graph Engine. Preserves M3 bbox exactly.
        No graph metadata, no column detection, no edge construction.
        """
        structured_pages = []
        for page in document.pages:
            tokens = []
            for idx, region in enumerate(page.regions):
                token = SemanticSpatialToken(
                    token_id=region.id,
                    text=region.text,
                    block_type="unknown",
                    bbox=BoundingBox.from_tuple(region.bbox),
                    confidence=region.confidence,
                    reading_order=idx,
                    page_number=page.page_number,
                    source_region_id=region.source_region_id or region.id,
                    column_id=-1,
                    spatial_metadata=region.spatial_metadata.copy() if hasattr(region, "spatial_metadata") else {}
                )
                tokens.append(token)
            
            structured_pages.append(
                StructuredPage(page_number=page.page_number, tokens=tokens, spatial_graph=None)
            )

        return StructuredDocument(
            source_document_id=document.source_document_id,
            pages=structured_pages,
            metadata=document.metadata
        )
