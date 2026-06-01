# M3 — Document Layout Analysis & Structural Intelligence
# See agents.md §MODULE_CONTRACTS → M3
#
# Files:
#   interface.py       — layout_analysis(PreprocessedDocument) -> LayoutDocument [PUBLIC]
#   types.py           — confidence thresholds, region type enum, overlay colors
#   config_hook.py     — reads confidence_threshold, layout.model
#   detector.py        — layout model runner (LayoutLMv3 / Detectron2)
#   engine_registry.py — swappable model backend registry
#   region_filter.py   — confidence filtering (§ALGO-CONF: 0.5 discard, 0.7 flag)
#   column_detector.py — single vs multi-column detection
#   reading_order.py   — §ALGO-RO: deterministic reading order reconstruction
#   box_merger.py      — §ALGO-BB: IoU-based bounding box merge (threshold=0.3)
#   semantic_grouper.py — rule-based header/paragraph/footer/table classification
