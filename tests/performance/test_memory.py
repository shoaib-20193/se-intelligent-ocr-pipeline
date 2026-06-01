# tests/performance/test_memory.py
# Performance tests — RAM usage profiling
# See agents.md §PERFORMANCE_REQUIREMENTS → Memory Constraints (CON-5: min 8GB RAM)
#
# Test cases:
#   test_peak_ram_does_not_exceed_threshold_for_single_doc
#   test_ocr_model_not_reloaded_between_documents
#   test_large_batch_memory_does_not_grow_unboundedly
