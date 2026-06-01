# src/evaluation/README.md
# M9 — Validation, Benchmarking & Quality Assurance Framework
# See agents.md §MODULE_CONTRACTS → M9, §EVALUATION_SYSTEM
#
# Files:
#   interface.py      — evaluate(GroundTruth, StructuredDocument, PipelineResult) -> EvaluationReport [PUBLIC]
#   types.py          — IOU_MATCH_THRESHOLD=0.5, WER/Precision/Recall/F1 targets
#   iou_matcher.py    — §ALGO-EVAL: IoU-based TP/FP/FN region matching
#   metrics_engine.py — Precision, Recall, F1-Score formulas
#   wer_calculator.py — §ALGO-WER: Levenshtein word-level WER computation
#   dataset_loader.py — FUNSD, SROIE, custom ground-truth loader
#   report_builder.py — assembles final EvaluationReport from all metric sources
#
# Constraint: metrics computed ONLY if ground truth is provided (BR-1 FR-9)
# Accuracy target: metrics must match manual verification +-5% (FR-9)
