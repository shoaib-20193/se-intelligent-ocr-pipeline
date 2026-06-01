# m4_ocr/paddle_engine.py
# PaddleOCR concrete implementation of base_engine.BaseOCREngine
# See agents.md §MODULE_CONTRACTS → M4, CON-2
#
# Constraint: PaddleOCR is the mandatory default OCR engine (CON-2).
# Model must be lazy-loaded once per session and cached.
# Batch inference is mandatory — single-region sequential calls prohibited.
# Target accuracy: >= 85% on clean printed English (FR-4 testable metric)
