# tests/integration/test_export_formats.py
# Integration test — all export formats produce correct files
# See agents.md §MODULE_CONTRACTS → M6
#
# Test cases:
#   test_json_file_valid_and_parseable
#   test_csv_file_contains_expected_table_rows
#   test_xlsx_file_opens_with_correct_sheet_count
#   test_docx_file_contains_heading1_paragraphs_tables
#   test_markdown_file_contains_gfm_table_syntax
#   test_all_formats_exported_when_all_selected
