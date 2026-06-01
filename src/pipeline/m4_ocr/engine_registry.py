"""
src/pipeline/m4_ocr/engine_registry.py
Registry for OCR backends.
"""
from enum import Enum

class OCRBackend(Enum):
    PADDLE = "paddle"
    # Future backends (e.g., Tesseract) can be added here.
