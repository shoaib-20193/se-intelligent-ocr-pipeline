# m5_reconstruct/paragraph_merger.py
# Paragraph merging for M5 — implements §ALGO-PARA
# See agents.md §CORE_ALGORITHMS → §ALGO-PARA
#
# Merge condition (both must hold):
#   A.type == "paragraph"  AND  B.type == "paragraph"
#   abs(A.y2 - B.y1) < PARA_MERGE_GAP_PX        (B directly below A)
#   abs(A.x1 - B.x1) < PARA_ALIGN_TOLERANCE_PX  (left-aligned)
#
# Active only when PostProcessConfig.merge_paragraphs = True
# Only adjacent pairs <= 2 lines apart are merged (BR-1 from FR-5)
#
# Merge result:
#   text = A.text + " " + B.text
#   bbox = (min(A.x1,B.x1), A.y1, max(A.x2,B.x2), B.y2)
