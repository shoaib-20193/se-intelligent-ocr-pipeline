# gui/panels/orchestration_panel.py
# Bottom Panel — Orchestration Tracker
# See agents.md §MODULE_CONTRACTS → M8 Tab 1 → Bottom Panel
# Maps to: M7 (PipelineResult.stage_metrics + log stream)
#
# Elements:
#   - Stage Tracker bar: Ingest -> Enhance -> Layout -> OCR -> Reconstruct -> Export
#   - Console: real-time timestamped logs from M7 (via GUIHandler in logging layer)
