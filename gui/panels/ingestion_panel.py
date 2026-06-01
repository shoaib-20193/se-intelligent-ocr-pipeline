# gui/panels/ingestion_panel.py
# Left Panel — Ingestion & Queue
# See agents.md §MODULE_CONTRACTS → M8 Tab 1 → Left Panel
# Maps to: M1 (ProcessingRequest.input_path)
#
# Elements:
#   - Drag-and-drop file zone
#   - "Select Files..." button -> opens file browser
#   - Queue list widget (QueueList) with per-document status badges:
#     "queued" | "processing" | "done" | "failed"
