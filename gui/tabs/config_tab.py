# gui/tabs/config_tab.py
# Tab 2 — Configuration
# See agents.md §MODULE_CONTRACTS → M8 Tab 2, §UI_TO_SYSTEM_MAPPING
#
# Sections (one per module):
#   M1: max_pages, max_file_size_mb, allowed format checkboxes
#   M2: denoise toggle, deskew toggle, thresholding toggle, resize_scale slider
#   M3: model selector (LayoutLMv3|Detectron2), confidence threshold slider
#   M4: device toggle (CPU|GPU), language selector (en|ur|ar)
#   M5: merge_paragraphs toggle, grammar_correction toggle, confidence input
#   M6: format checkboxes, output directory browser
#
# Constraint: writes to YAML config files only via ConfigController
# Zero processing logic in this file
