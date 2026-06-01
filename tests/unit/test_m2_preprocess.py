# tests/unit/test_m2_preprocess.py
# Unit tests for M2 — Adaptive Image Enhancement & Normalization Engine
# See agents.md §MODULE_CONTRACTS → M2
#
# Test cases:
#   test_denoise_reduces_noise_when_enabled
#   test_denoise_skipped_when_disabled
#   test_deskew_corrects_skew_within_1_degree
#   test_deskew_skipped_when_disabled
#   test_clahe_always_applied
#   test_thresholding_applied_when_enabled
#   test_thresholding_skipped_when_disabled
#   test_resize_scale_applied_correctly
#   test_perspective_correction_applied_when_enabled
#   test_output_image_dimensions_unchanged_at_scale_1
