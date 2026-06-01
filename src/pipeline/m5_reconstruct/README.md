# M5 — Text Refinement & Structural Reconstruction Engine
# See agents.md §MODULE_CONTRACTS → M5
#
# Files:
#   interface.py          — reconstruct(RecognizedDocument, PostProcessConfig) -> StructuredDocument [PUBLIC]
#   types.py              — MIN_TEXT_LENGTH, PARA_MERGE_GAP_PX, PARA_ALIGN_TOLERANCE_PX
#   config_hook.py        — reads confidence_threshold, grammar_correction, merge_paragraphs
#   confidence_filter.py  — §ALGO-CONF: remove regions below ocr_confidence threshold
#   artifact_cleaner.py   — §ALGO-ARTIFACT: empty text, short text, non-printable char removal
#   paragraph_merger.py   — §ALGO-PARA: spatial adjacency-based paragraph merging
#   table_reconstructor.py — §ALGO-TABLE: heuristic grid-based table row/col reconstruction
#   section_grouper.py    — groups header + paragraphs into Section objects
#   grammar_corrector.py  — grammar correction hook (TODO: engine undefined)
#
# Output domain: text + structure only. No image arrays in StructuredDocument.
# Mismerged paragraph rate target: <= 5% (FR-5)
