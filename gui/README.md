# gui/README.md
# M8 — Interactive Control & Configuration Interface
# See agents.md §MODULE_CONTRACTS → M8, §UI_TO_SYSTEM_MAPPING
#
# Structure:
#   app.py              — application entry point; initializes framework + launches MainWindow
#   main_window.py      — top-level window; hosts 3-tab QTabWidget
#   tabs/
#     processing_tab.py   — Tab 1: Document Processing (M1 M3 M5 M7)
#     config_tab.py       — Tab 2: Configuration (M1-M6 config fields)
#     benchmarking_tab.py — Tab 3: Benchmarking / Evaluation (M9)
#   panels/
#     ingestion_panel.py      — drag-drop zone + queue list (M1)
#     viewer_panel.py         — stage selector + bbox overlay canvas (M3)
#     inspector_panel.py      — structure tree + quick-edit textbox (M5)
#     orchestration_panel.py  — stage tracker bar + log console (M7)
#   widgets/
#     stage_tracker_widget.py — pipeline stage progress bar
#     bbox_canvas.py          — image + colored bbox overlay renderer
#     queue_list.py           — document queue with status badges
#     structure_tree.py       — expandable section/table tree
#     log_console.py          — timestamped log entry viewer
#   controllers/
#     pipeline_controller.py  — builds ProcessingRequest; calls M7 non-blocking
#     config_controller.py    — reads/writes YAML config files
#     export_controller.py    — builds ExportConfig; triggers M6
#
# HARD RULES:
#   - Zero processing logic in any GUI file
#   - GUI constructs ProcessingRequest -> passes to M7 -> polls for status
#   - Config editor writes to YAML only
#   - Export enabled only after status = "success" | "partial"
#   - Only one active processing session per batch
