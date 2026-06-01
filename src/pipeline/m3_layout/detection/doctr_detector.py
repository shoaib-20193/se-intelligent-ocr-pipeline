"""
Lazy-loaded DocTR geometry extraction backend.
M3 is STRICTLY spatial/geometric only.
"""
import logging
import numpy as np
from typing import List
from src.data_model.layout import Region
from src.data_model.preprocessed import ProcessedPage
from .bbox_normalizer import normalize_bbox
from .crop_extractor import extract_crop_ref

logger = logging.getLogger(__name__)

class DocTRDetector:
    def __init__(self):
        self._model = None
    
    def _initialize_model(self):
        if self._model is None:
            logger.info("Initializing DocTR db_resnet50 detector backend...")
            from doctr.models import detection_predictor
            # Lazy load the pure detection model; prevents OCR semantics
            self._model = detection_predictor(arch='db_resnet50', pretrained=True)
            
    def detect_page(self, page: ProcessedPage, document_id: str) -> List[Region]:
        """
        Runs DocTR detection on a single page, returning purely spatial Region objects.
        Returns raw word-level regions.
        """
        self._initialize_model()
        
        image = page.clean_image
        height, width = image.shape[:2]
        
        # Ensure RGB 3-channel for DocTR
        if len(image.shape) == 2:
            import cv2
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            import cv2
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        # Inference: pure geometry extraction
        out = self._model([image])
        
        regions = []
        page_preds = out[0]
        
        if isinstance(page_preds, dict):
            words = page_preds.get("words", np.array([]))
            for i, box in enumerate(words):
                if len(box) >= 5:
                    xmin, ymin, xmax, ymax, conf = box[:5]
                elif len(box) == 4:
                    xmin, ymin, xmax, ymax = box
                    conf = 1.0
                else:
                    continue
                
                abs_bbox = normalize_bbox((float(xmin), float(ymin), float(xmax), float(ymax)), width, height)
                
                # Exclude invalid zero-area boxes
                if abs_bbox[2] <= abs_bbox[0] or abs_bbox[3] <= abs_bbox[1]:
                    continue
                    
                page_id = f"{document_id}_p{page.page_number}"
                r = Region(
                    id=f"p{page.page_number}-w{i}",
                    bbox=abs_bbox,
                    polygon=None,
                    confidence=float(conf),
                    type="text_block",
                    spatial_metadata={"word_level": True},
                    crop_ref=extract_crop_ref(page_id, abs_bbox)
                )
                regions.append(r)
        
        return regions
