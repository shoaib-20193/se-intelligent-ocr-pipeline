# tests/regression/test_evaluation_baseline.py
# Regression test — EvaluationReport must not degrade below baseline
# See agents.md §MODULE_CONTRACTS → M9, §PERFORMANCE_REQUIREMENTS
#
# Baseline targets (from agents.md §EVALUATION_SYSTEM):
#   Precision >= 0.85
#   Recall    >= 0.80
#   F1-Score  >= 0.82
#   WER       <= 0.15
#   IoU       >= 0.80 (FR-3)
#
# Test cases:
#   test_precision_not_below_baseline
#   test_recall_not_below_baseline
#   test_f1_not_below_baseline
#   test_wer_not_above_baseline
#   test_layout_iou_not_below_baseline
