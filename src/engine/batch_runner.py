# src/engine/batch_runner.py
# M7 — Batch document processing loop
# See agents.md §MODULE_CONTRACTS → M7 Batch Mode, §EXECUTION_ENGINE → Batch Mode
#
# Public function:
#   run_batch(requests: list[ProcessingRequest]) -> list[PipelineResult]
#
# Rules:
#   - Call orchestrator.run(request) per document
#   - On exception for document D:
#       catch(exception)
#       log(document_id, stage, error)
#       mark D.status = "failed"
#       continue to D+1 (do not halt batch)
#   - Batch success rate must be >= 85% (NFR-1)
#   - Return all PipelineResult objects (including failed ones)
#   - TODO: Define BatchResult aggregate schema
#   - TODO: Define concurrency model (currently sequential per document)
