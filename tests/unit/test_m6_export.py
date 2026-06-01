# tests/unit/test_m6_export.py
# Unit tests for M6 — Structured Output Serialization & Export Framework
# See agents.md §MODULE_CONTRACTS → M6
#
# Test cases:
#   test_json_export_produces_valid_file
#   test_csv_export_contains_table_rows
#   test_xlsx_export_creates_one_sheet_per_table
#   test_docx_export_headings_are_heading1_style
#   test_markdown_export_tables_use_gfm_pipe_syntax
#   test_schema_validation_runs_before_write
#   test_atomic_write_uses_temp_then_rename
#   test_failed_format_does_not_block_other_formats
#   test_export_summary_contains_absolute_paths
#   test_export_status_partial_when_one_format_fails
