# tests/unit/test_m7_orchestrator.py
# Unit tests for M7 — Pipeline Orchestration & Execution Engine
# See agents.md §MODULE_CONTRACTS → M7, §EXECUTION_ENGINE
#
# Test cases:
#   test_stage_order_is_m1_through_m6
#   test_exception_in_m2_marks_document_failed
#   test_exception_does_not_halt_batch
#   test_stage_metrics_recorded_per_stage
#   test_pipeline_result_status_success_on_clean_doc
#   test_pipeline_result_status_failed_on_corrupt_doc
#   test_profile_loaded_from_yaml_before_execution
#   test_batch_success_rate_above_85_percent
