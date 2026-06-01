# M6 — Structured Output Serialization & Export Framework
# See agents.md §MODULE_CONTRACTS → M6
#
# Files:
#   interface.py       — export(StructuredDocument, ExportConfig) -> ExportSummary [PUBLIC]
#   types.py           — SUPPORTED_FORMATS, EXPORT_STATUS_ENUM
#   config_hook.py     — reads formats, output_directory from ExportConfig
#   schema_validator.py — pre-write schema completeness validation (mandatory)
#   atomic_writer.py   — write to temp file -> rename (no partial writes)
#   json_exporter.py   — full StructuredDocument JSON tree
#   csv_exporter.py    — tables-only CSV (Table.rows flattened)
#   xlsx_exporter.py   — tables with formatting, one sheet per Table
#   docx_exporter.py   — full document with Heading1, paragraphs, DOCX tables
#   markdown_exporter.py — full document in GitHub-flavored markdown
#
# Isolation rule: failure in one format must not block other formats.
