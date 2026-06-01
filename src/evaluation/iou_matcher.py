# src/evaluation/iou_matcher.py
# IoU-based region matching for M9 — implements §ALGO-EVAL
# See agents.md §CORE_ALGORITHMS → §ALGO-EVAL
#
# Function:
#   match_regions(predicted: list[Region], ground_truth: list[Region]) -> MatchResult
#
# Rule: predicted matches ground-truth iff IoU >= IOU_MATCH_THRESHOLD (0.5)
#
# IoU formula (same as §ALGO-BB):
#   intersection = max(0, min(A.x2,B.x2)-max(A.x1,B.x1)) *
#                  max(0, min(A.y2,B.y2)-max(A.y1,B.y1))
#   union = area_A + area_B - intersection
#   IoU   = intersection / union
#
# MatchResult: { TP: int, FP: int, FN: int }
