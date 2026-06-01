"""
M2 — Denoiser: OCR-oriented adaptive denoising.
agents.md §MODULE_CONTRACTS → M2 Step 2 (active if denoise=True)

V2.3 changes vs V2.0:
- Replaced default GaussianBlur with OCR-safe fastNlMeansDenoising
- Added blur_score estimation via Laplacian variance
- Added adaptive skip logic for already-sharp / extremely-blurry images
- Gaussian blur retained as "gaussian" strategy (legacy/speed profiles only)
- API backward-compatible: denoise(image) still works with defaults

V2.4 critical fix patch:
- _BLUR_SCORE_THRESHOLD reduced 80 → 45 (better usable/degraded separation)
- _is_already_blurry renamed → _is_low_quality (semantically accurate)
- Adaptive logic corrected:
    OLD: skip denoising when blur_score < threshold (was blocking recovery on blurry images)
    NEW: skip ONLY when blur_score > 120 (already sharp → denoising unnecessary)
         force recovery mode when blur_score < 35 (extreme blur → bilateral forced)
- Bilateral filter DEMOTED to last-resort/recovery-only role; nlmeans remains primary
- blur_score appended to strategy string for downstream debug traceability
- blur_score computed exactly once per denoise() call (no redundant Laplacian passes)
- adaptive=True, blur_safe=True set as defaults (safer out-of-the-box behaviour)
"""
from __future__ import annotations
import cv2
import numpy as np
from src.utils.image_utils import to_grayscale

# ── Blur estimation thresholds (calibrated against real document corpus) ──────────
# Laplacian variance classification (V2.5 recalibrated — real scan values):
#
#   < 300         → severe blur / extreme degradation
#   300 – 700     → low quality / mobile / aged scan
#   700 – 1000    → normal document (standard scan)
#   > 1000        → clean high-DPI scan — denoising skipped
#
# Effective decision logic (RECOVERY checked before SKIP_HIGH):
#   blur_score < 1000  → force bilateral recovery (RECOVERY=1000 catches everything below)
#   blur_score > 1000  → skip denoising (SKIP_HIGH=700 triggers for scores above 1000)
#
_BLUR_SCORE_THRESHOLD: float = 300.0    # lower bound of normal range (reference)
_BLUR_SCORE_SKIP_HIGH: float = 700.0    # above this → skip IF not already in recovery
_BLUR_SCORE_RECOVERY:  float = 1000.0   # below this → force bilateral recovery


def estimate_blur_score(image: np.ndarray) -> float:
    """
    Estimate image sharpness using Laplacian variance.

    Higher variance = sharper edges = normal denoising safe.
    Lower variance  = soft/blurry  = aggressive denoising may merge characters.

    Returns:
        Float ≥ 0. Lower = blurrier.
    """
    gray = to_grayscale(image)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def _is_low_quality(blur_score: float) -> bool:
    """
    Return True if the image is in the low-quality range (35–45).
    These images should still be processed — do NOT skip them.
    Previously named _is_already_blurry (renamed V2.4: blur_score
    reflects general quality, not blur alone).
    """
    return blur_score < _BLUR_SCORE_THRESHOLD


# ── Core denoising strategies ─────────────────────────────────────────────────

def _denoise_nlmeans(image: np.ndarray, h: int = 10) -> np.ndarray:
    """
    Non-local Means denoising — OCR primary strategy.

    Preserves text edges by averaging non-locally similar patches.
    Works on grayscale only; BGR input converted automatically.

    Args:
        image: uint8 ndarray (grayscale or BGR).
        h:     Filter strength (default 10). Lower = less smoothing.
    Returns:
        Denoised grayscale uint8 ndarray.
    """
    gray = to_grayscale(image)
    return cv2.fastNlMeansDenoising(
        gray, None,
        h=h,
        templateWindowSize=7,
        searchWindowSize=21,
    )


def _denoise_bilateral(image: np.ndarray) -> np.ndarray:
    """
    Bilateral filter — LAST RESORT / RECOVERY-ONLY strategy. (V2.4)

    IMPORTANT: bilateral is NO LONGER the default OCR denoising path.
    Use only when:
      1. blur_score < _BLUR_SCORE_RECOVERY (forced recovery mode), OR
      2. profile explicitly requests "bilateral" for sensor-noise documents.

    Warning: even at conservative settings (d=3, σ=25), bilateral filtering
    may soften text strokes and slightly increase character merging risk.
    Prefer nlmeans for all normal OCR denoising.

    V2.4 settings: d=3, σColor=25, σSpace=25 (OCR-safe; reduced from d=9, σ=75)

    Args:
        image: uint8 ndarray (grayscale or BGR).
    Returns:
        Filtered uint8 ndarray (same channels as input).
    """
    return cv2.bilateralFilter(image, d=3, sigmaColor=25, sigmaSpace=25)


def _denoise_gaussian(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Gaussian blur — legacy strategy. Fast but degrades blurry text.
    Use ONLY for clean, sharp scans where speed is the priority.
    blur_safe=True will override this to nlmeans automatically.
    """
    k = max(3, kernel_size)
    if k % 2 == 0:
        k += 1
    return cv2.GaussianBlur(image, (k, k), sigmaX=0)


# ── Public API ────────────────────────────────────────────────────────────────

def denoise(
    image: np.ndarray,
    strategy: str = "nlmeans",
    adaptive: bool = True,
    blur_safe: bool = True,
    kernel_size: int = 5,
    h: int = 10,
) -> tuple[np.ndarray, str]:
    """
    OCR-oriented denoising entry point. (V2.4 critical fix patch)

    Decision logic (evaluated in order, blur_score computed ONCE):

        1. Compute blur_score  (single Laplacian pass — no redundant calls)
        2. blur_safe guard     → force nlmeans if strategy="gaussian"
        3. Recovery mode       → if blur_score < 35, force bilateral regardless of strategy
        4. Adaptive skip       → if adaptive=True and blur_score > 120, skip (already sharp)
        5. Apply chosen strategy

    Args:
        image:       Input uint8 ndarray.
        strategy:    "nlmeans" (default) | "bilateral" | "gaussian" | "none"
        adaptive:    If True, skip denoising when blur_score > 120 (already sharp).
                     Does NOT skip on blurry images (V2.4 fix — old logic was inverted).
        blur_safe:   If True, override "gaussian" → "nlmeans" to guard against
                     Gaussian over-smoothing on blurry documents.
        kernel_size: Gaussian kernel size (strategy="gaussian" only).
        h:           NlMeans filter strength (strategy="nlmeans" only).

    Returns:
        (processed_image, strategy_label)
        strategy_label includes blur_score for traceability:
        e.g. "nlmeans_blur=87.34" or "bilateral_recovery_mode_blur=22.10"
    """
    # ── Step 1: Compute blur_score ONCE ──────────────────────────────────────
    blur_score = estimate_blur_score(image)

    # ── Step 2: blur_safe guard (Gaussian → nlmeans override) ────────────────
    if blur_safe and strategy == "gaussian":
        strategy = "nlmeans"

    # ── Step 3: Recovery mode — extreme blur forces bilateral regardless ──────
    # blur_score < 35 = severely degraded; nlmeans may not be effective.
    # Bilateral at conservative settings handles extreme sensor noise safely.
    # This step executes BEFORE adaptive skip so recovery is never bypassed.
    if blur_score < _BLUR_SCORE_RECOVERY:
        result = _denoise_bilateral(image)
        return result, f"bilateral_recovery_mode_blur={blur_score:.2f}"

    # ── Step 4: Adaptive skip — image is already sharp, denoising wastes time ─
    # Only skip when blur_score > 120. Blurry images are NOT skipped (V2.4 fix).
    if adaptive and blur_score > _BLUR_SCORE_SKIP_HIGH:
        return image, f"skipped_already_sharp_blur={blur_score:.2f}"

    # ── Step 5: Apply chosen strategy ─────────────────────────────────────────
    if strategy == "none":
        return image, f"none_blur={blur_score:.2f}"
    elif strategy == "nlmeans":
        return _denoise_nlmeans(image, h=h), f"nlmeans_blur={blur_score:.2f}"
    elif strategy == "bilateral":
        return _denoise_bilateral(image), f"bilateral_blur={blur_score:.2f}"
    elif strategy == "gaussian":
        return _denoise_gaussian(image, kernel_size=kernel_size), f"gaussian_blur={blur_score:.2f}"
    else:
        return image, f"unknown_strategy_skipped({strategy})_blur={blur_score:.2f}"
