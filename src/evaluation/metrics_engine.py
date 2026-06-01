# src/evaluation/metrics_engine.py
# Precision, Recall, F1-Score computation for M9
# See agents.md §EVALUATION_SYSTEM, §ALGO-EVAL
#
# Formulas:
#   Precision = TP / (TP + FP)
#   Recall    = TP / (TP + FN)
#   F1        = 2 * Precision * Recall / (Precision + Recall)
#
# Input: MatchResult from iou_matcher
# Output: {precision: float, recall: float, f1_score: float}
