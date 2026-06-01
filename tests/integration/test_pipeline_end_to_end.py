# tests/integration/test_pipeline_end_to_end.py
# Integration test — full pipeline M1 -> M2 -> M3 -> M4 -> M5 -> M6
# See agents.md §MODULE_CONTRACTS → M9 Test Suite Requirements
# Uses mock OCR engine (deterministic) to avoid real inference dependency
#
# Test cases:
#   test_clean_pdf_produces_structured_document
#   test_clean_image_produces_structured_document
#   test_pipeline_result_has_all_stage_metrics
#   test_output_files_written_to_disk
#   test_export_summary_status_is_success
#   test_zero_region_page_handled_without_crash
