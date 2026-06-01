# M2 — Adaptive Image Enhancement & Normalization Engine
# See agents.md §MODULE_CONTRACTS → M2
#
# Files:
#   interface.py   — preprocess(Document, ProfileConfig) -> PreprocessedDocument [PUBLIC]
#   types.py       — CLAHE constants, skew target constant
#   config_hook.py — reads denoise, deskew, thresholding, resize_scale, perspective_correction
#   denoiser.py    — Gaussian noise reduction (step 2, toggleable)
#   deskewer.py    — skew correction to +-1 deg (step 3, toggleable)
#   enhancer.py    — CLAHE contrast enhancement (step 4, always active)
#   thresholder.py — Otsu/adaptive thresholding (step 5, toggleable)
#   resizer.py     — resize by scale factor (step 6)
#   perspective.py — perspective correction (step 7, toggleable)
