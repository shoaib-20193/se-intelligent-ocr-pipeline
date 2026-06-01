# gui/controllers/export_controller.py
# Triggers M6 export from GUI
# See agents.md §MODULE_CONTRACTS → M8, §UI_TO_SYSTEM_MAPPING → Export button
#
# Responsibilities:
#   - Build ExportConfig from Tab 2 format/directory selections
#   - Call pipeline.m6_export.interface.export()
#   - Update queue status badge on export completion
#
# Constraint: Export button enabled only after PipelineResult.status = "success"|"partial"
