# m4_ocr/config_hook.py
# Reads M4-relevant fields from OCRConfig
# See agents.md §DATA_MODEL → OCRConfig
#
# Consumed fields:
#   config.device     -> str  ("cpu" | "gpu")
#   config.language   -> str  ("en" | "ur" | "ar")
#   config.batch_size -> int  (number of region crops per inference call)
