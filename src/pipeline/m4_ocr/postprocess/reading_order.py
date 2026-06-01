"""
src/pipeline/m4_ocr/postprocess/reading_order.py
Normalizes OCR extraction order deterministically.
"""
from typing import List, Tuple

def normalize_ocr_reading_order(
    ocr_results: List[Tuple[List[List[float]], Tuple[str, float]]]
) -> List[Tuple[List[List[float]], Tuple[str, float]]]:
    """
    Sorts PaddleOCR 2.7.3 bounding boxes deterministically:
    Top-to-bottom (y-coordinate), then left-to-right (x-coordinate).
    
    PaddleOCR bounding box format:
    [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    """
    if not ocr_results:
        return []

    def get_sort_key(item):
        box, _ = item
        # Calculate bounding box centroid or top-left corner
        # Using top-left y, then top-left x
        y1 = box[0][1]
        x1 = box[0][0]
        
        # Round y1 to group lines roughly together (e.g., within 10 pixels)
        # This prevents slight vertical jitter from messing up left-to-right order
        rounded_y1 = round(y1 / 10.0) * 10
        return (rounded_y1, x1)

    return sorted(ocr_results, key=get_sort_key)
