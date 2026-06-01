# tests/mocks/mock_ocr_engine.py
# Deterministic mock OCR engine — replaces PaddleOCR in tests
# See agents.md §MODULE_CONTRACTS → M9 Test Suite: "Mocked inference tests"
#
# Implements: src/pipeline/m4_ocr/base_engine.BaseOCREngine
#
# Behaviour:
#   load_model()  -> no-op
#   run_batch(crops) -> returns fixed deterministic (text, confidence) per crop
#   All returned ocr_confidence values > 0.5 by default (to pass confidence filter)
