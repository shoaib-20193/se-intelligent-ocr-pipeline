# tests/unit/test_m1_ingest.py
# Unit tests for M1 — Document Ingestion & Input Management
# See agents.md §MODULE_CONTRACTS → M1, §MODULE_CONTRACTS → M9 Test Suite
#
# Test cases (one per public interface / processing rule):
#   test_valid_pdf_ingested_successfully
#   test_valid_image_ingested_successfully
#   test_unsupported_format_rejected
#   test_file_exceeding_size_limit_rejected
#   test_file_exceeding_page_limit_rejected
#   test_corrupt_file_rejected_without_crash
#   test_metadata_extracted_correctly
#   test_document_id_is_uuid
#   test_all_pages_normalized_to_bgr
#   test_batch_directory_scan_returns_all_valid_files
