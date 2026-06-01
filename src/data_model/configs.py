"""
ProfileConfig, OCRConfig, PostProcessConfig, ExportConfig
agents.md §DATA_MODEL
V2.4: Added sharpening, morphology, and adaptive threshold tuning fields.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ProfileConfig:
    """
    Named preprocessing profile — agents.md §CONFIGURATION_SCHEMA.
    V2.3: denoise_strategy, adaptive_denoise, blur_safe_mode, threshold_mode, clahe_clip_limit
    V2.4: sharpen, sharpen_strength, adaptive_block_size, adaptive_C,
           morphology_opening, morphology_kernel_size, morphology_closing
    """
    profile_id: str = "fast_draft"

    # ── Core preprocessing flags (agents.md §MODULE_CONTRACTS → M2) ──────────
    denoise: bool = False
    deskew: bool = False
    thresholding: bool = False
    resize_scale: float = 1.0
    perspective_correction: bool = False
    grammar_correction: bool = False
    merge_paragraphs: bool = False

    # ── Layout + OCR confidence gate ─────────────────────────────────────────
    confidence_threshold: float = 0.5

    # ── V2.3: OCR-oriented denoising controls ─────────────────────────────────
    denoise_strategy: str = "nlmeans"
    # ENUM: "gaussian" | "nlmeans" | "bilateral" | "none"

    adaptive_denoise: bool = False
    # Skip denoising when blur_score (Laplacian variance) < 80

    blur_safe_mode: bool = False
    # Hard guard: forces nlmeans even if profile says "gaussian"

    # ── V2.3: Thresholding mode ───────────────────────────────────────────────
    threshold_mode: str = "otsu"
    # ENUM: "otsu" | "adaptive"

    # ── V2.3: CLAHE aggressiveness ────────────────────────────────────────────
    clahe_clip_limit: float = 1.5
    # Conservative default (1.5). Lower = less stroke thickening.

    # ── V2.4: Unsharp masking (sharpening before CLAHE) ──────────────────────
    sharpen: bool = False
    # Applies unsharp masking to restore edges BEFORE CLAHE + thresholding.
    # Position in pipeline: after deskew, before CLAHE.
    # Recommended: True for blurred_document and mobile_photo profiles.

    sharpen_strength: float = 0.5
    # Unsharp mask alpha: 0.3 = subtle; 0.5 = moderate; 0.8 = aggressive.
    # High values amplify halos — keep ≤ 0.6 for OCR text.

    # ── V2.4: Adaptive threshold tuning ──────────────────────────────────────
    adaptive_block_size: int = 31
    # Neighbourhood block size for adaptive threshold.
    # Smaller = finer local computation; must be odd. Range: 11–51.
    # Use 15–21 for blurry documents to reduce over-merging.

    adaptive_C: int = 10
    # Constant subtracted from weighted mean before threshold.
    # Higher C → more aggressive separation (thinner strokes, more gaps).
    # Use 15–20 for blurry documents to break character welds.

    # ── V2.4: Morphological operations (after thresholding) ──────────────────
    morphology_opening: bool = False
    # Morphological opening (erode → dilate) after binarisation.
    # Removes tiny bridges/connections between adjacent characters.
    # Recommended: True for blurred_document. Disabled for clean scans.

    morphology_kernel_size: int = 2
    # Kernel size for morphological operations (default 2×2).
    # Conservative: 2×2 removes micro-bridges without destroying thin fonts.
    # Use 1×1 for very thin fonts (thin stroke documents).

    morphology_closing: bool = False
    # Morphological closing (dilate → erode) after opening.
    # Fills small gaps in broken strokes.
    # Rarely needed — enable only when strokes fragment after threshold.


@dataclass
class OCRConfig:
    """agents.md §DATA_MODEL → OCRConfig"""
    device: str = "cpu"
    language: str = "en"
    batch_size: int = 8


@dataclass
class PostProcessConfig:
    """agents.md §DATA_MODEL → PostProcessConfig"""
    confidence_threshold: float = 0.5
    grammar_correction: bool = False
    merge_paragraphs: bool = False


@dataclass
class ExportConfig:
    """agents.md §DATA_MODEL → ExportConfig"""
    formats: list[str] = field(default_factory=lambda: ["json"])
    output_directory: str = "./data/output"
