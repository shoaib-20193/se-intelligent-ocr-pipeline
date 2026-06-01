"""
M2 — Adaptive Decision Engine: quality-tier based preprocessing parameter routing.
V2.5 NEW module — agents.md §MODULE_CONTRACTS → M2 V2.5

Pipeline position: BEFORE all preprocessing steps (per page, per image)

Architecture:
    1. Compute blur_score via Laplacian variance (single pass)
    2. Classify image into quality tier: blurred / low_quality / normal / sharp
    3. Apply tier-specific parameter overrides on top of the base profile
    4. Return adapted ProfileConfig — original profile is NEVER mutated

Design principle (V2.5):
    Blur_score is a first-class routing signal, not just a logging value.
    The same base profile produces DIFFERENT parameter sets per image type.
    One universal preprocessing config is intentionally avoided.

Quality tier thresholds (calibrated against real document scans):
    < 100        → blurred       (extreme degradation / out-of-focus)
    100 – 400    → low_quality   (mobile photo / aged scan / soft focus)
    400 – 450    → normal        (standard scanned document)
    > 450        → sharp         (clean digital scan / high-DPI)

These values correspond to the denoiser's _BLUR_SCORE_RECOVERY and
_BLUR_SCORE_SKIP_HIGH thresholds — kept aligned to prevent contradictory
decisions between the decision engine and the denoiser's own logic.
"""
from __future__ import annotations
from dataclasses import replace

import numpy as np

from src.data_model.configs import ProfileConfig
from src.pipeline.m2_preprocess.denoiser import estimate_blur_score

# ── Quality tier thresholds (calibrated against real document corpus) ──────────────
# Note: these thresholds are independent from denoiser._BLUR_SCORE_RECOVERY /
# _BLUR_SCORE_SKIP_HIGH — both modules use blur_score but for separate decisions.
TIER_BLURRED_MAX:     float = 300.0    # < 300   → severely blurred
TIER_LOW_QUALITY_MAX: float = 700.0    # 300–700 → low quality / mobile
TIER_NORMAL_MAX:      float = 1000.0   # 700–1000 → standard scan
# > 1000 → sharp / high-DPI clean scan

# ── Tier-specific parameter override tables ────────────────────────────────────
# Each table is applied as a delta on top of the base ProfileConfig.
# Only fields that need tier-specific values are listed — everything else
# inherits from the base profile unchanged.

_OVERRIDES_BLURRED: dict = {
    # Blurred tier: maximize character separability
    # sharpen first to restore edges, then adaptive threshold with high C to break welds
    "sharpen":              True,
    "sharpen_strength":     0.5,
    "threshold_mode":       "adaptive",
    "adaptive_block_size":  19,          # fine local windows for soft text
    "adaptive_C":           18,          # aggressive separation constant
    "morphology_opening":   True,        # break remaining micro-bridges
    "morphology_kernel_size": 2,
    "morphology_closing":   False,
    "clahe_clip_limit":     1.0,         # minimal CLAHE to avoid halo amplification
}

_OVERRIDES_LOW_QUALITY: dict = {
    # Low quality tier: moderate adaptation
    # adaptive threshold handles uneven illumination; no morphology needed
    "sharpen":              False,
    "threshold_mode":       "adaptive",
    "adaptive_block_size":  25,
    "adaptive_C":           14,
    "morphology_opening":   False,
    "morphology_kernel_size": 2,
}

_OVERRIDES_NORMAL: dict = {
    # Normal tier: profile is used as-is
    # No overrides — the profile was designed for this input class
}

_OVERRIDES_SHARP: dict = {
    # Sharp tier: minimal processing — document is already clean
    # Disable operations that risk degrading clean strokes
    "sharpen":              False,
    "morphology_opening":   False,
    "morphology_closing":   False,
}


def classify_image_quality(blur_score: float) -> str:
    """
    Classify image into a quality tier based on Laplacian variance.

    Returns:
        "blurred"     — severe quality degradation (< 100)
        "low_quality" — mobile / aged / soft (100–400)
        "normal"      — standard scan (400–450)
        "sharp"       — clean high-quality scan (> 450)
    """
    if blur_score < TIER_BLURRED_MAX:
        return "blurred"
    elif blur_score < TIER_LOW_QUALITY_MAX:
        return "low_quality"
    elif blur_score < TIER_NORMAL_MAX:
        return "normal"
    else:
        return "sharp"


def _apply_overrides(profile: ProfileConfig, overrides: dict) -> ProfileConfig:
    """
    Return a new ProfileConfig with override fields applied.
    Original profile is never mutated (dataclasses.replace creates a copy).
    """
    if not overrides:
        return profile
    return replace(profile, **overrides)


def adapt_profile(
    image: np.ndarray,
    profile: ProfileConfig,
) -> tuple[ProfileConfig, float, str]:
    """
    Core V2.5 adaptive decision entry point.

    Computes blur_score once, classifies image quality, applies tier-specific
    parameter overrides to produce an image-specific ProfileConfig.

    IMPORTANT: if profile.adaptive_denoise is False, tier-based overrides
    for denoising parameters are still applied (adaptive_denoise controls
    the denoiser's internal skip logic, not this engine's routing).

    Args:
        image:   Input image (grayscale or BGR uint8 ndarray).
        profile: Base ProfileConfig loaded from YAML.

    Returns:
        (adapted_profile, blur_score, image_class)
        adapted_profile — new ProfileConfig with tier-specific parameters applied
        blur_score      — Laplacian variance (for logging / downstream tracing)
        image_class     — quality tier label (for logging / audit trail)
    """
    blur_score = estimate_blur_score(image)
    image_class = classify_image_quality(blur_score)

    overrides_map = {
        "blurred":     _OVERRIDES_BLURRED,
        "low_quality": _OVERRIDES_LOW_QUALITY,
        "normal":      _OVERRIDES_NORMAL,
        "sharp":       _OVERRIDES_SHARP,
    }
    overrides = overrides_map[image_class]
    adapted = _apply_overrides(profile, overrides)

    return adapted, blur_score, image_class
