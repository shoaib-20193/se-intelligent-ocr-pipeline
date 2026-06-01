"""
src/pipeline/m4_ocr/contracts/ocr_runtime_contracts.py
Explicit DTOs isolating M4 OCR configuration from orchestrator kwargs.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class LegacyPaddleConfig:
    """Strict legacy PaddleOCR 2.7.3 structure for runtime configuration."""
    language: str = "en"
    use_angle_cls: bool = True
    device: str = "cpu"
    cpu_threads: int = 4
    enable_mkldnn: bool = False
