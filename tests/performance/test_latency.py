# tests/performance/test_latency.py
# Performance tests — latency per page against NFR-3, NFR-4 targets
# See agents.md §PERFORMANCE_REQUIREMENTS
#
# NFR-3: <= 6-8 seconds per page on GPU-enabled system
# NFR-4: <= 2 seconds per page for interactive OCR preview
# Batch: <= 7 minutes for 50 pages on GPU
#
# Test cases:
#   test_single_page_latency_within_gpu_budget
#   test_interactive_ocr_preview_within_2_seconds
#   test_50_page_batch_within_7_minutes
#   test_stage_metrics_latency_recorded_per_stage
