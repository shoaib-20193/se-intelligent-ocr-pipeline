# src/evaluation/interface.py
# Public contract for M9 — Validation, Benchmarking & Quality Assurance Framework
# See agents.md §MODULE_CONTRACTS → M9
#
# Public function:
#   evaluate(ground_truth: GroundTruthDocument,
#            structured: StructuredDocument,
#            pipeline_result: PipelineResult) -> EvaluationReport
#
# Processing steps (ordered):
#   1. Load ground-truth document from user-specified path
#   2. Match predicted regions vs ground-truth regions using IoU (§ALGO-EVAL)
#   3. Compute layout Precision, Recall, F1-Score
#   4. Compute WER from OCR text vs ground-truth text (§ALGO-WER)
#   5. Record latency_per_page from PipelineResult.stage_metrics
#   6. Record ram_usage_mb from process RSS memory peak
#   7. Return EvaluationReport
#
# Constraint: metrics computed ONLY if ground truth is provided (BR-1 from FR-9)
