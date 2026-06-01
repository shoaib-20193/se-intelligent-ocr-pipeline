"""
Preprocessing Validation Framework — V2.2
Batch-capable preprocessing diff tool with isolated artifact directories.

Usage:
    python -m tests.visual.test_preprocessing_diff
        → generates synthetic test image and processes it

    python -m tests.visual.test_preprocessing_diff path/to/image.png
        → processes a single image file

    python -m tests.visual.test_preprocessing_diff path/to/directory/
        → batch-processes all supported images in the directory (recursive)

Output layout:
    data/debug/preprocess/stages/{stem}/    per-stage images for each input
    data/debug/preprocess/visual_diffs/     side-by-side raw vs processed diffs
    data/debug/preprocess/synthetic/        auto-generated synthetic test inputs

Artifact isolation rules:
    - data/test_inputs/  → clean input images only (never written by this script)
    - data/debug/        → generated artifacts only (never read as input)
    - data/output/       → pipeline exports only (never read as input)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

# ── Path bootstrap ────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

import cv2
import numpy as np

from src.data_model.configs import ProfileConfig
from src.pipeline.m2_preprocess.denoiser import denoise
from src.pipeline.m2_preprocess.deskewer import deskew
from src.pipeline.m2_preprocess.sharpen import sharpen             # V2.4
from src.pipeline.m2_preprocess.enhancer import enhance_clahe
from src.pipeline.m2_preprocess.thresholder import threshold
from src.pipeline.m2_preprocess.morphology import apply_morphology  # V2.4
from src.pipeline.m2_preprocess.resizer import resize
from src.pipeline.m2_preprocess.perspective import correct_perspective
from src.pipeline.m2_preprocess.adaptive_decision import adapt_profile  # V2.5
from src.utils.image_utils import to_grayscale, side_by_side, save_debug_image, safe_load

# ── Directory constants ───────────────────────────────────────────────────────
_DBG_ROOT   = _ROOT / "data" / "debug" / "preprocess"
_STAGES_DIR = _DBG_ROOT / "stages"
_DIFFS_DIR  = _DBG_ROOT / "visual_diffs"
_SYNTH_DIR  = _DBG_ROOT / "synthetic"

# Directories that contain generated artifacts — never reprocess these
_ARTIFACT_DIRS: tuple[Path, ...] = (
    _ROOT / "data" / "debug",
    _ROOT / "data" / "output",
)

# Supported input file extensions
_SUPPORTED_EXT: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
)

# Substrings in filenames that identify generated artifact files
_ARTIFACT_NAME_PATTERNS: frozenset[str] = frozenset({
    "_DIFF", "_raw", "_grayscale", "_denoised", "_deskewed",
    "_clahe", "_threshold", "_resized", "_perspective", "_skipped",
    "_final_processed", "synthetic_document",
})

# Default validation profile — full OCR-oriented preprocessing enabled (V2.4)
_VALIDATION_PROFILE = ProfileConfig(
    profile_id="high_accuracy_validation",
    denoise=True,
    denoise_strategy="nlmeans",
    adaptive_denoise=True,
    blur_safe_mode=False,
    deskew=True,
    sharpen=False,
    sharpen_strength=0.5,
    thresholding=True,
    threshold_mode="otsu",
    adaptive_block_size=31,
    adaptive_C=10,
    morphology_opening=False,
    morphology_kernel_size=2,
    morphology_closing=False,
    resize_scale=1.0,
    perspective_correction=False,
    clahe_clip_limit=1.5,
)


# ── Result type ───────────────────────────────────────────────────────────────

class ProcessResult(NamedTuple):
    path: Path
    status: str    # "success" | "skipped" | "failed"
    reason: str = ""


# ── Artifact detection ────────────────────────────────────────────────────────

def _is_artifact(path: Path) -> bool:
    """
    Return True if this file is a known generated artifact and must be skipped.

    Two checks:
    1. Path is inside a known artifact/output directory tree.
    2. Filename contains a known generated-artifact pattern substring.
    """
    resolved = path.resolve()
    for art_dir in _ARTIFACT_DIRS:
        try:
            resolved.relative_to(art_dir.resolve())
            return True
        except ValueError:
            pass

    for pattern in _ARTIFACT_NAME_PATTERNS:
        if pattern in path.stem:
            return True

    return False


# ── Image collection ──────────────────────────────────────────────────────────

def _collect_images(target: Path) -> list[Path]:
    """
    Collect all processable image paths from a file or directory.
    Skips artifact files automatically.
    Returns sorted list of absolute paths.
    """
    if target.is_file():
        if target.suffix.lower() in _SUPPORTED_EXT and not _is_artifact(target):
            return [target.resolve()]
        return []

    results: list[Path] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in _SUPPORTED_EXT:
            continue
        if _is_artifact(p):
            continue
        results.append(p.resolve())

    return results


# ── Synthetic image generation ────────────────────────────────────────────────

def _make_synthetic(noise_strength: int = 12) -> Path:
    """
    Generate a deterministic synthetic document image for pipeline testing.
    Stored in data/debug/preprocess/synthetic/ — isolated from real test inputs.

    Args:
        noise_strength: σ of Gaussian noise (default 12). Kept small for determinism.
    Returns:
        Path to the saved synthetic image.
    """
    _SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _SYNTH_DIR / "synthetic_document.png"

    h, w = 900, 650
    img = np.full((h, w), 242, dtype=np.uint8)

    # Simulated text lines with word-gap breaks
    for row in range(120, 800, 45):
        cv2.line(img, (60, row), (590, row), 25, 2)
        for x_gap in range(60, 590, 90):
            cv2.line(img, (x_gap, row), (x_gap + 20, row), 242, 3)

    # Pre-apply 3° clockwise skew to test deskew (deterministic angle)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -3.0, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderValue=242)

    # Reproducible Gaussian noise (fixed seed = 42)
    rng = np.random.default_rng(seed=42)
    noise = rng.integers(-noise_strength, noise_strength + 1, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(str(out_path), bgr)
    return out_path


# ── Single-image processing ───────────────────────────────────────────────────

def process_single(image_path: Path, profile: ProfileConfig) -> ProcessResult:
    """
    Run the full M2 preprocessing pipeline on one image.
    Saves per-stage images + side-by-side diff.

    Never raises — all errors are caught and returned as ProcessResult(failed).
    """
    print(f"\n  ── {image_path.name} ──")
    raw = safe_load(str(image_path))

    if raw is None:
        print(f"    [SKIP] Cannot load image: unreadable or corrupt")
        return ProcessResult(image_path, "skipped", "unreadable")

    stem = image_path.stem
    stage_dir = _STAGES_DIR / stem
    stage_dir.mkdir(parents=True, exist_ok=True)
    _DIFFS_DIR.mkdir(parents=True, exist_ok=True)

    img = raw.copy()
    ops_applied: list[str] = []

    try:
        # 00 — raw copy
        save_debug_image(raw, str(stage_dir / "00_raw.png"))

        # Step 0 — Adaptive Decision Engine [V2.5]
        # Classify image quality and override profile params before any processing.
        profile, blur_score_ad, image_class = adapt_profile(img, profile)
        print(f"    [adaptive]    class={image_class:<12}  blur_score={blur_score_ad:.1f}")
        print(f"    [params]      threshold={profile.threshold_mode}  "
              f"bs={profile.adaptive_block_size}  C={profile.adaptive_C}  "
              f"sharpen={profile.sharpen}  morph_open={profile.morphology_opening}  "
              f"clahe_clip={profile.clahe_clip_limit}")

        # Step 1 — Grayscale
        if profile.denoise or profile.thresholding:
            img = to_grayscale(img)
            save_debug_image(img, str(stage_dir / "01_grayscale.png"))
            ops_applied.append("grayscale")

        # Step 2 — Denoise (blur_score already computed by adapt_profile; use it)
        if profile.denoise:
            img, strat_used = denoise(
                img,
                strategy=profile.denoise_strategy,
                adaptive=profile.adaptive_denoise,
                blur_safe=profile.blur_safe_mode,
            )
            save_debug_image(img, str(stage_dir / "02_denoised.png"))
            ops_applied.append(f"denoise_{strat_used}")
            print(f"    [denoise]     strategy={strat_used}")

        # Step 3 — Deskew
        if profile.deskew:
            img, angle = deskew(img)
            save_debug_image(img, str(stage_dir / "03_deskewed.png"))
            ops_applied.append("deskew")
            print(f"    [deskew]      detected angle: {angle:+.2f}°")

        # Step 3.5 — Sharpen [V2.4] (before CLAHE)
        if profile.sharpen:
            img = sharpen(img, strength=profile.sharpen_strength)
            save_debug_image(img, str(stage_dir / "035_sharpened.png"))
            ops_applied.append(f"sharpen(s={profile.sharpen_strength})")

        # Step 4 — CLAHE (always active; aggressiveness from profile)
        img = enhance_clahe(img, clip_limit=profile.clahe_clip_limit)
        save_debug_image(img, str(stage_dir / "04_clahe.png"))
        ops_applied.append(f"clahe(clip={profile.clahe_clip_limit})")

        # Step 5 — Threshold (mode + parameters driven by profile)
        if profile.thresholding:
            img = threshold(
                img,
                mode=profile.threshold_mode,
                block_size=profile.adaptive_block_size,
                c_constant=profile.adaptive_C,
            )
            save_debug_image(img, str(stage_dir / "05_threshold.png"))
            mode_desc = profile.threshold_mode
            if profile.threshold_mode == "adaptive":
                mode_desc += f"(bs={profile.adaptive_block_size},C={profile.adaptive_C})"
            ops_applied.append(f"threshold_{mode_desc}")

        # Step 5.5–5.6 — Morphology [V2.4] (after binary)
        if profile.morphology_opening or profile.morphology_closing:
            img, morph_ops = apply_morphology(
                img,
                opening=profile.morphology_opening,
                closing=profile.morphology_closing,
                kernel_size=profile.morphology_kernel_size,
            )
            for step in morph_ops:
                save_debug_image(img, str(stage_dir / f"055_{step}.png"))
            ops_applied.extend(morph_ops)

        # Step 6 — Resize
        if abs(profile.resize_scale - 1.0) > 1e-6:
            img = resize(img, profile.resize_scale)
            save_debug_image(img, str(stage_dir / f"06_resized_x{profile.resize_scale}.png"))
            ops_applied.append(f"resize×{profile.resize_scale}")

        # Step 7 — Perspective correction
        if profile.perspective_correction:
            img, success = correct_perspective(img)
            label = "07_perspective" if success else "07_perspective_skipped"
            save_debug_image(img, str(stage_dir / f"{label}.png"))
            ops_applied.append("perspective" if success else "perspective(skipped)")
            print(f"    [perspective] applied: {success}")

        # 99 — final processed image
        save_debug_image(img, str(stage_dir / "99_final_processed.png"))

        # Side-by-side diff
        diff_img = side_by_side(raw, img, gap=30)
        diff_path = _DIFFS_DIR / f"{stem}_DIFF.png"
        save_debug_image(diff_img, str(diff_path))

        print(f"    [ops]         {' → '.join(ops_applied)}")
        print(f"    [stages dir]  {stage_dir}")
        print(f"    [diff]        {diff_path}")

        return ProcessResult(image_path, "success")

    except Exception as exc:
        print(f"    [ERROR] {type(exc).__name__}: {exc}")
        return ProcessResult(image_path, "failed", f"{type(exc).__name__}: {exc}")


# ── Batch runner ──────────────────────────────────────────────────────────────

def run_batch(images: list[Path], profile: ProfileConfig) -> None:
    """
    Process a list of images and print a structured batch summary on completion.
    Single-file failures never terminate the batch.
    """
    total = len(images)
    print(f"\n{'═' * 54}")
    print(f"  Preprocessing Validation — Batch Mode")
    print(f"{'═' * 54}")
    print(f"  Images to process : {total}")
    print(f"  Profile           : {profile.profile_id}")
    print(f"  Output root       : {_DBG_ROOT}")
    print(f"{'═' * 54}")

    results: list[ProcessResult] = []
    for i, path in enumerate(images, 1):
        print(f"\n  [{i}/{total}]", end="")
        result = process_single(path, profile)
        results.append(result)

    # ── Summary ───────────────────────────────────────────────────────────────
    successful = sum(1 for r in results if r.status == "success")
    skipped    = sum(1 for r in results if r.status == "skipped")
    failed     = sum(1 for r in results if r.status == "failed")

    print(f"\n{'═' * 54}")
    print(f"  BATCH SUMMARY")
    print(f"{'═' * 54}")
    print(f"  Total     : {total}")
    print(f"  ✅ Success : {successful}")
    print(f"  ⏭  Skipped : {skipped}")
    print(f"  ❌ Failed  : {failed}")
    if failed:
        print(f"\n  Failed files:")
        for r in results:
            if r.status == "failed":
                print(f"    ✗ {r.path.name}  ({r.reason})")
    print(f"{'═' * 54}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg is None:
        # No input → generate synthetic document and process it
        synth_path = _make_synthetic()
        print(f"\n  [synthetic] Generated: {synth_path}")
        images = [synth_path]
    else:
        target = Path(arg).resolve()
        images = _collect_images(target)
        if not images:
            print(f"\n  [ERROR] No processable images found at: {target}")
            print(f"          (Supported: {sorted(_SUPPORTED_EXT)})")
            print(f"          (Artifact files are automatically excluded)")
            sys.exit(1)

    run_batch(images, _VALIDATION_PROFILE)
