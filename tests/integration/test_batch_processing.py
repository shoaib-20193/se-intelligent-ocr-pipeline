# tests/integration/test_batch_processing.py
# Integration test — batch mode with exception isolation
# See agents.md §EXECUTION_ENGINE → Batch Mode, NFR-1
#
# Test cases:
#   test_batch_with_all_valid_docs_succeeds
#   test_corrupt_doc_in_batch_does_not_halt_remaining
#   test_batch_success_rate_above_85_percent
#   test_failed_doc_marked_failed_in_results
#   test_all_pipeline_results_returned_including_failed
