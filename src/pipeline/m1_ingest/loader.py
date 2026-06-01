# m1_ingest/loader.py
# File loading and PDF-to-image conversion for M1
# See agents.md §MODULE_CONTRACTS → M1
#
# Responsibilities:
#   - Open image files as np.ndarray
#   - Convert PDF pages to np.ndarray images (one per page)
#   - Support recursive directory scanning for batch mode
#   - TODO: Streaming support for large files (chunk size undefined)
#   - TODO: Document type profiling before full processing
