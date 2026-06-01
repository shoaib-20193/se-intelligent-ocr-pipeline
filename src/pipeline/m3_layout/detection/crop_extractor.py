"""
Crop Extractor — generates lightweight crop references to prevent memory explosion.
"""

def extract_crop_ref(page_id: str, bbox: tuple[int, int, int, int]) -> dict:
    """
    Generates a lightweight crop_ref dictionary indicating where this region 
    exists on the source image, rather than duplicating the ndarray in memory.
    M4 will use this to lazy-extract the crop right before OCR inference.
    """
    return {
        "page_id": page_id,
        "bbox": list(bbox)
    }
