# gui/controllers/pipeline_controller.py
# Builds ProcessingRequest and calls M7 orchestrator (non-blocking)
# See agents.md §MODULE_CONTRACTS → M8 GUI Constraints
#
# Responsibilities:
#   - Build ProcessingRequest from GUI inputs
#   - Call engine.orchestrator.run() or engine.batch_runner.run_batch()
#   - Poll M7 for status updates (non-blocking — must not freeze GUI)
#   - Emit status signals back to GUI panels
#
# Constraint: only ONE active processing session per batch (BR-1 from FR-8)
# Export controls enabled ONLY after pipeline status = "success" | "partial" (BR-2)
