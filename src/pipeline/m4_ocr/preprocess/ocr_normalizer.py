"""
src/pipeline/m4_ocr/preprocess/ocr_normalizer.py
Light OCR-safe preprocessing layer.
Operations limited to: uint8 norm, grayscale/contrast stabilization, crop padding.
"""
import cv2
import numpy as np

MIN_CROP_W = 8
MIN_CROP_H = 8

def normalize_and_pad_crop(image: np.ndarray, bbox: list[int], max_w: int, max_h: int) -> np.ndarray | None:
    """
    Extracts, normalizes, and pads the crop from the clean image.
    Returns None if the crop is too small or invalid.
    """
    x1, y1, x2, y2 = bbox
    
    # Calculate padding
    width = x2 - x1
    height = y2 - y1
    
    if width < MIN_CROP_W or height < MIN_CROP_H:
        return None
        
    pad_x = int(width * 0.02)
    pad_y = int(height * 0.08)
    
    # Clip padded bounding box against page boundaries
    px1 = max(0, x1 - pad_x)
    py1 = max(0, y1 - pad_y)
    px2 = min(max_w, x2 + pad_x)
    py2 = min(max_h, y2 + pad_y)
    
    crop = image[py1:py2, px1:px2]
    
    if crop.size == 0:
        return None
        
    # Light Normalization: Ensure uint8
    if crop.dtype != np.uint8:
        crop = cv2.normalize(crop, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
    # Grayscale/Contrast stabilization (optional light norm, avoiding binarization)
    if len(crop.shape) == 3 and crop.shape[2] == 3:
        # Convert to grayscale to simplify OCR
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
    # Convert back to BGR for PaddleOCR which expects 3 channels
    crop_bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        
    return crop_bgr
