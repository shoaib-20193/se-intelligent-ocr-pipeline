from dataclasses import dataclass, field
from typing import Dict

@dataclass
class PipelineMetrics:
    """
    Centralized telemetry tracking for the entire M1->M4 orchestrator run.
    """
    total_runtime_s: float = 0.0
    stage_runtimes_s: Dict[str, float] = field(default_factory=dict)
    
    total_pages_processed: int = 0
    total_regions_processed: int = 0
    
    ocr_crops_accepted: int = 0
    ocr_crops_rejected: int = 0
    
    recoverable_failures: int = 0
    fatal_failures: int = 0

    def record_stage_time(self, stage_name: str, duration: float):
        self.stage_runtimes_s[stage_name] = duration

    def add_recoverable_failure(self):
        self.recoverable_failures += 1

    def add_fatal_failure(self):
        self.fatal_failures += 1
