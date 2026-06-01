# gui/panels/viewer_panel.py
# Center Panel — Visual Viewer
# See agents.md §MODULE_CONTRACTS → M8 Tab 1 → Center Panel
# Maps to: M1 (Raw), M2 (Preprocessed), M3 (Layout Overlay), M4/M5 (OCR Text)
#
# Elements:
#   - Stage selector: Raw | Preprocessed | Layout Overlay | OCR Text
#   - BBoxCanvas: renders document image + color-coded region overlays
#   - Region type toggles: per-type visibility on/off
#
# Overlay colors (§UI_TO_SYSTEM_MAPPING):
#   header=Blue, paragraph=Green, table=Yellow/Amber
#   figure=TODO, footer=TODO
