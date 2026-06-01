"""
src/pipeline/m4_ocr/dto/recognizer_adapter.py
Maps raw outputs to DTOs and performs OCR-level normalization.
"""
import copy
import math
from src.data_model.layout import Region
from src.data_model.ocr import RecognizedRegion

def normalize_ocr_output(text: str, confidence: float) -> tuple[str, float]:
    """
    Normalizes text and clamps confidence.
    """
    if text is None:
        return "", 0.0
        
    text = str(text).strip()
    
    if math.isnan(confidence) or math.isinf(confidence):
        confidence = 0.0
        
    confidence = max(0.0, min(1.0, float(confidence)))
    
    return text, confidence

def map_to_recognized_region(source_region: Region, text: str, confidence: float) -> RecognizedRegion:
    """
    Constructs a RecognizedRegion, strictly copying M3 reading order and metadata.
    """
    # Strict fallback in case reading_order is missing, though M3 guarantees it.
    reading_order = source_region.spatial_metadata.get("reading_order", -1)
    
    # Deep copy metadata to prevent accidental cross-stage mutation
    new_metadata = copy.deepcopy(source_region.spatial_metadata)
    
    return RecognizedRegion(
        id=source_region.id,
        bbox=source_region.bbox,
        text=text,
        confidence=confidence,
        source_region_id=source_region.id,
        reading_order=reading_order,
        crop_ref=source_region.crop_ref,
        spatial_metadata=new_metadata
    )
