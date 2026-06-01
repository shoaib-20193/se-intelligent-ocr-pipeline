"""
src/pipeline/m4_ocr/interface.py
Primary orchestrator for the M4 OCR Recognition Layer.
Maps LayoutDocument -> RecognizedDocument.
"""
import logging
from src.data_model.layout import LayoutDocument
from src.data_model.ocr import RecognizedDocument, RecognizedPage
from src.pipeline.m4_ocr.batching.page_runner import PageRunner
from src.pipeline.m4_ocr.filtering.confidence_filter import ConfidenceFilter
from src.pipeline.m4_ocr.telemetry.ocr_metrics import OCRMetrics
from src.pipeline.m4_ocr.postprocess.spatial_matcher import match_ocr_to_regions
from src.pipeline.m4_ocr.contracts.ocr_runtime_contracts import LegacyPaddleConfig

logger = logging.getLogger(__name__)


class M4OCREngine:
    def __init__(self, confidence_threshold: float = 0.5, init_config: LegacyPaddleConfig = None):
        self.runner = PageRunner(init_config=init_config)
        self.filter = ConfidenceFilter(threshold=confidence_threshold)

    def recognize_document(self, layout_doc: LayoutDocument, clean_images: dict) -> RecognizedDocument:
        """
        Executes OCR layer.
        clean_images must be a dict mapping page_number -> np.ndarray (the clean images from M2).
        """
        logger.info(f"[M4] Starting OCR for document: {layout_doc.document_id}")

        recognized_pages = []
        metrics = OCRMetrics()

        for layout_page in layout_doc.pages:
            page_num = layout_page.page_number
            clean_image = clean_images.get(page_num)

            if clean_image is None:
                logger.error(f"[M4] Clean image for page {page_num} not provided. Skipping OCR.")
                recognized_pages.append(RecognizedPage(page_number=page_num, regions=[], raw_text=""))
                continue

            # 1. Run full-page OCR — returns sorted [(box, (text, conf)), ...]
            raw_ocr_results = self.runner.process_page(clean_image, metrics)

            # 2. Reconcile OCR output back onto canonical M3 regions
            #    M3 geometry is preserved. M4 text is attached to M3 regions.
            recognized_regions = match_ocr_to_regions(raw_ocr_results, layout_page.regions)

            # 3. Filter by confidence threshold
            filtered_regions = self.filter.filter_regions(recognized_regions, metrics)

            # 4. Re-sort by M3 reading_order to guarantee determinism
            filtered_regions.sort(key=lambda r: r.reading_order)

            # 5. Assemble raw_text in reading order
            raw_text = "\n".join(r.text for r in filtered_regions if r.text)

            recognized_pages.append(RecognizedPage(
                page_number=page_num,
                regions=filtered_regions,
                raw_text=raw_text,
                page_width=layout_page.metadata.get("page_width", 800),
                page_height=layout_page.metadata.get("page_height", 1000)
            ))

        metrics.finish()
        logger.info(
            f"[M4] OCR Complete. "
            f"{metrics.accepted_outputs} accepted, {metrics.rejected_outputs} rejected, "
            f"{metrics.failed_calls} failed. Avg Conf: {metrics.average_confidence:.2f}"
        )

        return RecognizedDocument(
            source_document_id=layout_doc.document_id,
            pages=recognized_pages,
            metadata=layout_doc.metadata
        )
