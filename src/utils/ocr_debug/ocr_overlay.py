"""
src/utils/ocr_debug/ocr_overlay.py
Generates visual debug overlays for OCR results on page-level images.
No per-crop debug images.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from src.data_model.ocr import RecognizedPage

DEBUG_DIR = Path("data/debug/ocr")

def generate_ocr_overlay(page: RecognizedPage, clean_image: np.ndarray, doc_id: str):
    """
    Draws bounding boxes, reading order, and recognized text on a copy of the image.
    Saves to data/debug/ocr/
    """
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a copy to prevent mutation
    overlay = clean_image.copy()
    
    for r in page.regions:
        x1, y1, x2, y2 = r.bbox
        
        # Draw box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw reading order index
        order = r.reading_order
        cv2.putText(overlay, f"[{order}]", (x1, max(0, y1 - 10)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    
        # Draw recognized text and confidence
        text_disp = r.text[:20] + "..." if len(r.text) > 20 else r.text
        conf_str = f"({r.confidence:.2f})"
        cv2.putText(overlay, f"{text_disp} {conf_str}", (x1, y2 + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                    
    out_path = DEBUG_DIR / f"{doc_id}_page_{page.page_number}_ocr.jpg"
    cv2.imwrite(str(out_path), overlay)
    
