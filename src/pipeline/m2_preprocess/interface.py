"""
M2 — Adaptive Image Enhancement & Normalisation Engine [V2.5 — Adaptive Decision Engine]

Stage order (agents.md §MODULE_CONTRACTS → M2, V2.5 extension):
    Step 0: Adaptive Decision  [V2.5 NEW] (classify image, override profile params)
    Step 1: BGR → Grayscale       (if denoise=True OR thresholding=True)
    Step 2: Denoise               (if denoise=True  → profile.denoise_strategy)
    Step 3: Deskew                (if deskew=True)
    Step 3.5: Sharpen [V2.4]     (if sharpen=True → conditionally set by decision engine)
    Step 4: CLAHE                 (ALWAYS → profile.clahe_clip_limit)
    Step 5: Threshold             (if thresholding=True → tier-adapted params)
    Step 5.5: Morph Open [V2.4]   (if morphology_opening=True → tier-adapted)
    Step 5.6: Morph Close [V2.4]  (if morphology_closing=True)
    Step 6: Resize                (by profile.resize_scale)
    Step 7: Perspective           (if perspective_correction=True)

V2.5 change: blur_score is now a first-class routing signal.
    The adaptive decision engine classifies each page image into a quality tier
    and applies tier-specific parameter overrides before any processing begins.
    The base profile is NEVER mutated — each page gets its own adapted copy.
"""
from __future__ import annotations
from typing import Any

import numpy as np

from src.data_model.document import Document
from src.data_model.preprocessed import PreprocessedDocument, ProcessedPage, PreprocessingMeta
from src.data_model.configs import ProfileConfig
from src.utils.image_utils import to_grayscale

from src.pipeline.m2_preprocess.adaptive_decision import adapt_profile          # V2.5
from src.pipeline.m2_preprocess.denoiser import denoise, estimate_blur_score
from src.pipeline.m2_preprocess.deskewer import deskew
from src.pipeline.m2_preprocess.sharpen import sharpen
from src.pipeline.m2_preprocess.enhancer import enhance_clahe
from src.pipeline.m2_preprocess.thresholder import threshold as apply_threshold
from src.pipeline.m2_preprocess.morphology import apply_morphology
from src.pipeline.m2_preprocess.resizer import resize
from src.pipeline.m2_preprocess.perspective import correct_perspective


def _process_page(
    raw_image: Any,
    page_number: int,
    profile: ProfileConfig,
) -> ProcessedPage:
    """
    Run the full V2.4 M2 preprocessing pipeline on a single page image.
    All strategy choices driven by ProfileConfig. No hardcoded behaviour.
    Graceful passthrough if raw_image is None.
    """
    meta = PreprocessingMeta(
        scale_applied=profile.resize_scale,
        clahe_clip_limit_used=profile.clahe_clip_limit,
        denoise_strategy_used="not_run",
    )

    if raw_image is None:
        meta.operations_applied.append("skipped_no_image")
        return ProcessedPage(
            page_number=page_number,
            clean_image=None,
            preprocess_meta=meta,
        )

    img: np.ndarray = raw_image.copy()

    # ── Step 0: Adaptive Decision Engine [V2.5] ───────────────────────────────
    # Classify image quality and apply tier-specific parameter overrides.
    # base profile is never mutated — each page gets its own adapted copy.
    profile, blur_score_computed, image_class = adapt_profile(img, profile)
    meta.blur_score = blur_score_computed
    meta.operations_applied.append(f"adaptive_decision({image_class},blur={blur_score_computed:.1f})")

    # ── Step 1: Colour space → Grayscale ────────────────────────────────────
    needs_gray = profile.denoise or profile.thresholding
    if needs_gray:
        img = to_grayscale(img)
        meta.operations_applied.append("grayscale")

    # ── Step 2: Denoise ──────────────────────────────────────────────────────
    if profile.denoise:
        blur_score = estimate_blur_score(img)
        meta.blur_score = blur_score

        img, strategy_used = denoise(
            img,
            strategy=profile.denoise_strategy,
            adaptive=profile.adaptive_denoise,
            blur_safe=profile.blur_safe_mode,
        )
        meta.denoise_strategy_used = strategy_used
        meta.operations_applied.append(f"denoise_{strategy_used}")

    # ── Step 3: Deskew ───────────────────────────────────────────────────────
    if profile.deskew:
        img, angle = deskew(img)
        meta.skew_angle_deg = angle
        meta.operations_applied.append("deskew")

    # ── Step 3.5: Unsharp masking [V2.4] ─────────────────────────────────────
    if profile.sharpen:
        img = sharpen(img, strength=profile.sharpen_strength)
        meta.operations_applied.append(f"sharpen(s={profile.sharpen_strength})")

    # ── Step 4: CLAHE (ALWAYS ACTIVE, configurable aggressiveness) ───────────
    img = enhance_clahe(img, clip_limit=profile.clahe_clip_limit)
    meta.operations_applied.append(f"clahe(clip={profile.clahe_clip_limit})")

    # ── Step 5: Threshold (profile-driven mode + parameters) ─────────────────
    if profile.thresholding:
        img = apply_threshold(
            img,
            mode=profile.threshold_mode,
            block_size=profile.adaptive_block_size,
            c_constant=profile.adaptive_C,
        )
        thresh_desc = profile.threshold_mode
        if profile.threshold_mode == "adaptive":
            thresh_desc += f"(bs={profile.adaptive_block_size},C={profile.adaptive_C})"
        meta.operations_applied.append(f"threshold_{thresh_desc}")

    # ── Step 5.5–5.6: Morphological operations [V2.4] ────────────────────────
    if profile.morphology_opening or profile.morphology_closing:
        img, morph_ops = apply_morphology(
            img,
            opening=profile.morphology_opening,
            closing=profile.morphology_closing,
            kernel_size=profile.morphology_kernel_size,
        )
        meta.operations_applied.extend(morph_ops)

    # ── Step 6: Resize ───────────────────────────────────────────────────────
    if abs(profile.resize_scale - 1.0) > 1e-6:
        img = resize(img, profile.resize_scale)
        meta.operations_applied.append(f"resize×{profile.resize_scale}")

    # ── Step 7: Perspective correction ───────────────────────────────────────
    if profile.perspective_correction:
        img, success = correct_perspective(img)
        meta.perspective_corrected = success
        meta.operations_applied.append(
            "perspective" if success else "perspective_skipped"
        )

    # Add assertion per Validation_Guards
    assert img is not None, "clean_image must not be None after processing"

    return ProcessedPage(
        page_number=page_number,
        clean_image=img,
        raw_image=raw_image,
        preprocess_meta=meta,
    )


def preprocess(document: Document, profile: ProfileConfig) -> PreprocessedDocument:
    """
    M2 entry point. Applies profile-driven preprocessing to every page.
    Input:  Document, ProfileConfig
    Output: PreprocessedDocument
    """
    processed_pages = [
        _process_page(page.image, page.page_number, profile)
        for page in document.pages
    ]
    return PreprocessedDocument(
        metadata=document.metadata,
        pages=processed_pages,
    )
