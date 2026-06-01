"""
src/pipeline/m4_ocr/telemetry/ocr_metrics.py
Collects OCR runtime statistics.
"""
from dataclasses import dataclass, field
import time

@dataclass
class OCRMetrics:
    total_crops_processed: int = 0
    accepted_outputs: int = 0
    rejected_outputs: int = 0
    failed_calls: int = 0
    total_confidence: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0

    def add_accepted(self, confidence: float):
        self.total_crops_processed += 1
        self.accepted_outputs += 1
        self.total_confidence += confidence

    def add_rejected(self, confidence: float):
        self.total_crops_processed += 1
        self.rejected_outputs += 1
        self.total_confidence += confidence

    def add_failure(self):
        self.total_crops_processed += 1
        self.failed_calls += 1

    def finish(self):
        self.end_time = time.time()

    @property
    def average_confidence(self) -> float:
        if self.accepted_outputs + self.rejected_outputs == 0:
            return 0.0
        return self.total_confidence / (self.accepted_outputs + self.rejected_outputs)

    @property
    def total_elapsed_seconds(self) -> float:
        return (self.end_time or time.time()) - self.start_time

    @property
    def throughput_crops_per_second(self) -> float:
        elapsed = self.total_elapsed_seconds
        return self.total_crops_processed / elapsed if elapsed > 0 else 0.0
