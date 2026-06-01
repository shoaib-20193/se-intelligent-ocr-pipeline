# src/engine/README.md
# M7 — Pipeline Orchestration & Execution Engine
# See agents.md §MODULE_CONTRACTS → M7, §EXECUTION_ENGINE
#
# Files:
#   orchestrator.py  — run(ProcessingRequest) -> PipelineResult [PUBLIC]
#                      Calls M1->M2->M3->M4->M5->M6 in strict immutable order
#   batch_runner.py  — run_batch(list[ProcessingRequest]) -> list[PipelineResult]
#                      Exception isolation at document boundary (NFR-1: >=85% success)
#   stage_tracker.py — per-stage per-page latency + log entry collection
#   profile_loader.py — loads YAML ProfileConfig by profile_id
#
# Constraint: M7 does NOT transform data — coordinates transformation only.
# Stage order M1->M2->M3->M4->M5->M6 is IMMUTABLE at runtime.
