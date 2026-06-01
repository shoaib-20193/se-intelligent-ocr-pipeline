from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class M4RuntimeConfig:
    """Strict configuration model for M4 OCR engine.
    Only fields explicitly listed are allowed to be passed to PaddleOCR.
    """
    lang: str = "en"
    ocr_version: str = "PP-OCRv4"
    device: Literal["cpu", "gpu", "auto"] = "auto"
    enable_mkldnn:bool = False

    def resolve_device(self) -> str:
        """Map enable_gpu flag to actual device string.
        """
        return self.device

    def validate_engine_compatibility(self, version: str) -> str:
        valid_versions = {"PP-OCRv3", "PP-OCRv4", "PP-OCRv5"}
        if version not in valid_versions:
            raise ValueError(f"Invalid OCR version: {version}. Supported values are {list(valid_versions)}.")
        return version

    def normalize_ocr_version(self) -> str:
        VERSION_MAP = {
            "latest": "PP-OCRv5",
            "stable": "PP-OCRv4"
        }
        version = VERSION_MAP.get(self.ocr_version, self.ocr_version)
        return self.validate_engine_compatibility(version)


