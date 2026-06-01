# M4 — Recognition Engine Abstraction Layer (OCR)
# See agents.md §MODULE_CONTRACTS → M4
#
# Files:
#   interface.py      — recognize(LayoutDocument, OCRConfig) -> RecognizedDocument [PUBLIC]
#   types.py          — OCR_CONFIDENCE_DISCARD_THRESHOLD=0.5, DEFAULT_BATCH_SIZE=8
#   config_hook.py    — reads device, language, batch_size from OCRConfig
#   base_engine.py    — abstract OCR engine interface (load_model, run_batch)
#   paddle_engine.py  — PaddleOCR concrete implementation (default, CON-2)
#   engine_registry.py — pluggable engine name -> class mapping
#   batch_runner.py   — crop batching, batch submission, confidence discard
#
# Constraint: Model loaded once per session. Batch inference mandatory.
