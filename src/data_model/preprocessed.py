"""
PreprocessedDocument, ProcessedPage, PreprocessingMeta
agents.md §DATA_MODEL → PreprocessedDocument
V2.3: Added blur_score, denoise_strategy_used, clahe_clip_limit_used to PreprocessingMeta.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from src.data_model.document import DocumentMetadata


@dataclass
class PreprocessingMeta:
    """Records what operations ran and their results for a single page (V2.3)."""
    skew_angle_deg: float = 0.0               # detected skew angle (0.0 if deskew disabled)
    scale_applied: float = 1.0                # actual resize factor used
    perspective_corrected: bool = False       # True if 4-point warp was applied

    # V2.3 additions
    blur_score: float = -1.0                  # Laplacian variance; -1 = not measured
    denoise_strategy_used: str = "not_run"    # actual strategy used after adaptive checks
    clahe_clip_limit_used: float = 1.5        # CLAHE aggressiveness applied

    operations_applied: list[str] = field(default_factory=list)
    # ordered list of operations that ran, e.g.:
    # ["grayscale", "denoise_nlmeans", "deskew", "clahe(clip=1.5)", "threshold_adaptive"]


@dataclass
class ProcessedPage:
    page_number: int
    clean_image: Any = None                            # np.ndarray; None if no image yet
    raw_image: Any = None                              # np.ndarray; original unmodified image
    preprocess_meta: Optional[PreprocessingMeta] = field(default=None)


@dataclass
class PreprocessedDocument:
    metadata: DocumentMetadata                         # pass-through unchanged from Document
    pages: list[ProcessedPage] = field(default_factory=list)
