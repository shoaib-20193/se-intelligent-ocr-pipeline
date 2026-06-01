# m5_reconstruct/confidence_filter.py
# OCR confidence filtering for M5 — implements §ALGO-CONF (post-OCR stage)
# See agents.md §CORE_ALGORITHMS → §ALGO-CONF
#
# Rules:
#   Remove RecognizedRegion where ocr_confidence < PostProcessConfig.confidence_threshold
#   Default threshold: 0.5
