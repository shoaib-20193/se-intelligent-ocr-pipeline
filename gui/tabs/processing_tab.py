# gui/tabs/processing_tab.py
# Tab 1 — Document Processing
# See agents.md §MODULE_CONTRACTS → M8 Tab 1, §UI_TO_SYSTEM_MAPPING
#
# Layout (4 panels):
#   Left   — IngestionPanel    (drag-drop + queue list)
#   Center — ViewerPanel       (stage-selector + bbox canvas)
#   Right  — InspectorPanel    (structure tree + quick edit)
#   Bottom — OrchestrationPanel (stage tracker bar + console log)
#
# Maps to modules: M1, M3, M5, M7
# Constraint: no processing logic — delegates to PipelineController
