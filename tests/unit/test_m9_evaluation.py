# tests/unit/test_m9_evaluation.py
# Unit tests for M9 — Validation, Benchmarking & Quality Assurance Framework
# See agents.md §MODULE_CONTRACTS → M9, §EVALUATION_SYSTEM
#
# Test cases:
#   test_iou_computed_correctly_for_overlapping_boxes
#   test_iou_is_zero_for_non_overlapping_boxes
#   test_tp_fp_fn_counted_correctly
#   test_precision_formula_correct
#   test_recall_formula_correct
#   test_f1_formula_correct
#   test_wer_zero_for_identical_text
#   test_wer_correct_for_known_substitution
#   test_evaluation_report_fields_all_populated
#   test_metrics_not_computed_without_ground_truth
