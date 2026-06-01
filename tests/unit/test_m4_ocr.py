# tests/unit/test_m4_ocr.py
# Unit tests for M4 — Recognition Engine Abstraction Layer
# See agents.md §MODULE_CONTRACTS → M4
#
# Test cases:
#   test_ocr_model_loaded_once_per_session
#   test_regions_below_ocr_confidence_threshold_skipped
#   test_batch_inference_called_not_single_region
#   test_recognized_region_inherits_layout_confidence
#   test_recognized_region_inherits_region_id
#   test_cpu_device_selected_from_config
#   test_language_set_from_config
#   test_batch_size_respected
#   test_mock_engine_returns_deterministic_output
