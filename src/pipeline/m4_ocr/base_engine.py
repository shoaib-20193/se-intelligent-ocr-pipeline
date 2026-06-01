# m4_ocr/base_engine.py
# Abstract base class for OCR engines
# See agents.md §MODULE_CONTRACTS → M4 constraints
#
# Abstract interface:
#   load_model(device: str, language: str) -> None
#   run_batch(crops: list[np.ndarray]) -> list[tuple[str, float]]
#       returns: list of (text, ocr_confidence) per crop
#
# Constraint: PaddleOCR is default concrete implementation.
# Tesseract or custom engines must implement this interface only.
# No pipeline-level changes permitted when adding new engines.
