# m3_layout_cv_legacy — V3 Classical CV Layout Engine (Frozen)

**Status:** Frozen. Not part of the active pipeline. Preserved for rollback only.

## What this is
The original V3 M3 layout engine built on OpenCV morphological detection and heuristic
semantic grouping. Replaced in V3.1 by the DocTR pretrained detection backend.

## Rollback instructions
1. Install: `pip install opencv-python numpy`
2. In `src/pipeline/m3_layout/engine_registry.py`, set default backend to `"classical_cv"`
3. The classical CV engine requires no ML models or network access

## Architecture notes
- Detection: MORPH_CLOSE (35×2 horizontal + 3×18 vertical) + findContours
- Semantic grouping: position heuristics (top 18% = header, bottom 10% = footer)
- Column detection: x-projection occupancy clustering
- Reading order: §ALGO-RO band-sort (agents.md spec)
- Confidence: heuristic (aspect ratio + fill ratio), NOT a learned probability

## ⚠️ Important
Internal imports in this folder reference `src.pipeline.m3_layout.*`.
After renaming, those imports would need updating if the legacy engine is activated.
For rollback, use the `classical_cv` key via `engine_registry.get_detector("classical_cv")`.
Do NOT modify any file in this folder.
