"""
src/pipeline/m4_ocr/filtering/confidence_filter.py
Discards OCR results below the configurable threshold.
"""
from src.data_model.ocr import RecognizedRegion
from src.pipeline.m4_ocr.telemetry.ocr_metrics import OCRMetrics

class ConfidenceFilter:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def filter_regions(self, regions: list[RecognizedRegion], metrics: OCRMetrics) -> list[RecognizedRegion]:
        accepted = []
        for r in regions:
            if r.confidence >= self.threshold:
                accepted.append(r)
                metrics.add_accepted(r.confidence)
            else:
                metrics.add_rejected(r.confidence)
        return accepted
