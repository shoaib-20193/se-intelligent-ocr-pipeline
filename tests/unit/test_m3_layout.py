# tests/unit/test_m3_layout.py
# Unit tests for M3 — Document Layout Analysis & Structural Intelligence
# See agents.md §MODULE_CONTRACTS → M3, §CORE_ALGORITHMS → §ALGO-RO, §ALGO-BB
#
# Test cases:
#   test_regions_below_hard_discard_threshold_excluded
#   test_regions_in_warning_range_flagged_but_included
#   test_region_ids_assigned_in_correct_format
#   test_single_column_reading_order_correct
#   test_two_column_reading_order_correct
#   test_bounding_box_merge_above_iou_threshold
#   test_bounding_box_not_merged_below_iou_threshold
#   test_cropped_image_matches_bbox_coords
#   test_semantic_grouper_assigns_header_type
