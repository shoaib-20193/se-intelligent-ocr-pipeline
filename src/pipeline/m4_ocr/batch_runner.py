# m4_ocr/batch_runner.py
# Batch inference execution for M4
# See agents.md §MODULE_CONTRACTS → M4 step 4b
#
# Responsibilities:
#   - Collect all Region.cropped_image values per LayoutPage
#   - Split crops into batches of OCRConfig.batch_size
#   - Submit each batch to the active OCR engine
#   - Collect (text, ocr_confidence) per crop
#   - Discard results where ocr_confidence < OCR_CONFIDENCE_DISCARD_THRESHOLD (0.5)
