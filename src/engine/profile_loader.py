"""
profile_loader — Load ProfileConfig + derived configs from YAML.
V2.3: reads new OCR-oriented preprocessing fields.
See agents.md §CONFIGURATION_SCHEMA, §MODULE_CONTRACTS → M7 Step 1
"""
from __future__ import annotations
import os
import yaml
from src.data_model.configs import ProfileConfig, OCRConfig, PostProcessConfig, ExportConfig

_CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "profiles"
)


def load_profile(profile_id: str) -> tuple[ProfileConfig, OCRConfig, PostProcessConfig, ExportConfig]:
    """Load named profile from YAML; falls back to in-code defaults if file not found."""
    yaml_path = os.path.join(_CONFIG_DIR, f"{profile_id}.yaml")
    raw = {}
    if os.path.isfile(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

    pre  = raw.get("preprocessing", {})
    lay  = raw.get("layout", {})
    ocr  = raw.get("ocr", {})
    post = raw.get("postprocess", {})
    exp  = raw.get("export", {})

    profile = ProfileConfig(
        profile_id=raw.get("profile_id", profile_id),

        # Core preprocessing flags
        denoise=bool(pre.get("denoise", False)),
        deskew=bool(pre.get("deskew", False)),
        thresholding=bool(pre.get("thresholding", False)),
        resize_scale=float(pre.get("resize_scale", 1.0)),
        perspective_correction=bool(pre.get("perspective_correction", False)),

        # Post-processing flags
        grammar_correction=bool(post.get("grammar_correction", False)),
        merge_paragraphs=bool(post.get("merge_paragraphs", False)),

        # Confidence gate
        confidence_threshold=float(lay.get("confidence_threshold", 0.5)),

        # V2.3: OCR-oriented denoising controls
        denoise_strategy=str(pre.get("denoise_strategy", "nlmeans")),
        adaptive_denoise=bool(pre.get("adaptive_denoise", False)),
        blur_safe_mode=bool(pre.get("blur_safe_mode", False)),

        # V2.3: Thresholding mode
        threshold_mode=str(pre.get("threshold_mode", "otsu")),

        # V2.3: CLAHE aggressiveness
        clahe_clip_limit=float(pre.get("clahe_clip_limit", 1.5)),

        # V2.4: Unsharp masking
        sharpen=bool(pre.get("sharpen", False)),
        sharpen_strength=float(pre.get("sharpen_strength", 0.5)),

        # V2.4: Adaptive threshold tuning
        adaptive_block_size=int(pre.get("adaptive_block_size", 31)),
        adaptive_C=int(pre.get("adaptive_C", 10)),

        # V2.4: Morphological operations
        morphology_opening=bool(pre.get("morphology_opening", False)),
        morphology_kernel_size=int(pre.get("morphology_kernel_size", 2)),
        morphology_closing=bool(pre.get("morphology_closing", False)),
    )
    ocr_config = OCRConfig(
        device=str(ocr.get("device", "cpu")),
        language=str(ocr.get("language", "en")),
        batch_size=int(ocr.get("batch_size", 8)),
    )
    pp_config = PostProcessConfig(
        confidence_threshold=float(post.get("confidence_threshold", 0.5)),
        grammar_correction=bool(post.get("grammar_correction", False)),
        merge_paragraphs=bool(post.get("merge_paragraphs", False)),
    )
    exp_config = ExportConfig(
        formats=list(exp.get("formats", ["json"])),
        output_directory=str(exp.get("output_directory", "./data/output")),
    )
    return profile, ocr_config, pp_config, exp_config
