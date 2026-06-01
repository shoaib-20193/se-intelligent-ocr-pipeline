"""
src/pipeline/m4_ocr/engines/paddle_engine.py
Wraps PaddleOCR strictly for full-page text recognition.
"""
import numpy as np
import logging

from src.pipeline.m4_ocr.cache.session_manager import PaddleOCRSessionManager
from src.pipeline.m4_ocr.contracts.ocr_runtime_contracts import LegacyPaddleConfig
from src.pipeline.m4_ocr.postprocess.reading_order import normalize_ocr_reading_order

logger = logging.getLogger(__name__)

class PaddleEngineWrapper:
    def __init__(self, init_config: LegacyPaddleConfig):
        self.manager = PaddleOCRSessionManager()
        self.init_config = init_config

    def recognize_page(self, page_img: np.ndarray) -> list:
        """
        Recognizes text across a full page image matrix.
        Returns a deterministically sorted list of:
        [ ( [[x,y], [x,y], [x,y], [x,y]], (text, confidence) ), ... ]
        """
        if page_img is None:
            return []

        engine = self.manager.get_engine(init_config=self.init_config)
        
        # Must be contiguous for C++ backend stability
        working_img = np.ascontiguousarray(page_img.copy(), dtype=np.uint8)

        try:
            # Legacy PaddleOCR 2.7.3 .ocr() call
            # returns: [[[box_coords], (text, conf)], ...] for the page
            predictions = engine.ocr(working_img, cls=True)
            
            if not predictions:
                return []

            page_data = predictions[0] if len(predictions) > 0 and isinstance(predictions[0], list) else predictions
            
            if not page_data or page_data is None:
                return []

            # Format is typically [[box], [text, conf]] or [[box], (text, conf)]
            # Let's ensure standard format
            results = []
            for line in page_data:
                if isinstance(line, list) and len(line) >= 2:
                    box = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    conf = text_info[1]
                    results.append((box, (str(text), float(conf))))
            
            # Sort deterministically
            sorted_results = normalize_ocr_reading_order(results)
            return sorted_results

        except Exception as e:
            logger.error(f"[M4_CRITICAL] Full-page OCR failure: {e}")
            return []
