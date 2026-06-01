# tests/unit/test_m5_reconstruct.py
# Unit tests for M5 — Text Refinement & Structural Reconstruction Engine
# See agents.md §MODULE_CONTRACTS → M5, §CORE_ALGORITHMS → §ALGO-PARA, §ALGO-TABLE, §ALGO-ARTIFACT
#
# Test cases:
#   test_low_confidence_regions_removed
#   test_empty_text_regions_removed
#   test_short_text_below_min_length_removed
#   test_multiple_spaces_collapsed_to_single
#   test_nonprintable_chars_removed_preserving_newline_tab
#   test_adjacent_paragraphs_merged_when_enabled
#   test_paragraphs_not_merged_when_disabled
#   test_table_rows_reconstructed_correctly
#   test_sections_grouped_by_header_paragraph
#   test_title_set_from_first_header
#   test_raw_text_in_reading_order
