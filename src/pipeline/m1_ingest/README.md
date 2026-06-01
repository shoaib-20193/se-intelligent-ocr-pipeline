# M1 — Document Ingestion & Input Management
# See agents.md §MODULE_CONTRACTS → M1
#
# Files:
#   interface.py   — ingest(ProcessingRequest) -> Document  [PUBLIC CONTRACT]
#   types.py       — ALLOWED_EXTENSIONS, local type aliases
#   config_hook.py — reads constraints.max_pages, max_file_size_mb
#   validator.py   — file extension, size, page count, corruption checks
#   loader.py      — PDF-to-image conversion, image loading, dir scanning
#   normalizer.py  — BGR color space normalization
#
# Error behaviour: corrupt/rejected files are logged and skipped; no crash.
