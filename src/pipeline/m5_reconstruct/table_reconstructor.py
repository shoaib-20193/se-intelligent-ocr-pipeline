# m5_reconstruct/table_reconstructor.py
# Table reconstruction for M5 — implements §ALGO-TABLE
# See agents.md §CORE_ALGORITHMS → §ALGO-TABLE
#
# Input: RecognizedRegion where type = "table"
#
# Steps:
#   1. Identify horizontal whitespace bands (row separators)
#      row_separator = y-gap > ROW_GAP_THRESHOLD_PX between text blocks
#   2. Identify vertical whitespace bands (column separators)
#      col_separator = x-gap > COL_GAP_THRESHOLD_PX between text blocks
#   3. For each OCR text block:
#      cx = (x1+x2)/2,  cy = (y1+y2)/2
#      row_idx = index of row band containing cy
#      col_idx = index of col band containing cx
#   4. Fill rows[row_idx][col_idx] = text block content
#   5. Fill empty cells with ""
#
# ROW_GAP_THRESHOLD_PX: TODO (normalize by DPI)
# COL_GAP_THRESHOLD_PX: TODO (normalize by DPI)
#
# Output: Table { rows: list[list[str]] }
