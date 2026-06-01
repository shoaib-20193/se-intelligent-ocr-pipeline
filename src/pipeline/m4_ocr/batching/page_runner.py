"""
src/pipeline/m4_ocr/batching/page_runner.py
Executes OCR across pages while preserving orchestration abstraction.
"""
import logging
import numpy as np
from src.pipeline.m4_ocr.engines.paddle_engine import PaddleEngineWrapper
from src.pipeline.m4_ocr.telemetry.ocr_metrics import OCRMetrics
from src.pipeline.m4_ocr.contracts.ocr_runtime_contracts import LegacyPaddleConfig

logger = logging.getLogger(__name__)


class PageRunner:
    def __init__(self, init_config: LegacyPaddleConfig = None):
        if init_config is None:
            init_config = LegacyPaddleConfig()
        self.engine = PaddleEngineWrapper(init_config=init_config)
        self._engine_failed = False

    def process_page(self, page_img: np.ndarray, metrics: OCRMetrics) -> list:
        """
        Executes OCR on a single full page matrix.
        Returns the raw OCR results from paddle_engine:
        [ ( [[x,y]...], (text, conf) ), ... ]
        """
        if self._engine_failed:
            metrics.add_failure()
            return []

        try:
            results = self.engine.recognize_page(page_img)
            # Update metrics — pass confidence for each accepted result
            for _, (_, conf) in results:
                metrics.add_accepted(confidence=conf)
            return results
        except Exception as e:
            self._engine_failed = True
            logger.error(
                f"[M4_CRITICAL] OCR Engine page execution failed. "
                f"Aborting further pages. Error: {e}"
            )
            metrics.add_failure()
            return []
