# Architectural Knowledge Distillation Audit Report

This report documents the synthesis process used to construct `agents_V2.md` from the historical `agents.md` documentation base. The overarching goal was to distill years of architectural iterations into a pristine, canonical source of truth for the Intelligent Document Processing Pipeline.

## 1. Knowledge Retained
- **Core Pipeline DAG:** The strict `M1 → M2 → M3 → M4 → M5 → M6` execution flow and immutable data transfer object (DTO) boundaries were entirely preserved.
- **Data Contracts:** The structural schema of major DTOs (`ProcessingRequest`, `LayoutDocument`, `RecognizedDocument`, `StructuredDocument`, etc.) and their property invariants.
- **Module Responsibilities:** The clear semantic boundaries between M3 (geometry), M4 (raw OCR extraction), and M5 (semantic meaning and structural reconstruction).
- **M7 Execution Semantics:** The state machine design, fail-fast vs. retry recovery architectures, and orchestration constraints.
- **Operating Environment:** The strict Windows 11 Intel CPU requirements, 100% offline nature, and Python 3.10+ execution boundaries.
- **V3.2 M4/M7 Fixes:** The latest runtime configurations (PaddleOCR 2.7.3 pinning, ModelScope isolation, PyTorch pre-loading, CPU-only matrix execution) implemented to resolve deep-dependency faults.

## 2. Knowledge Removed
- **Unclassified Legacy Content:** Over 200KB of obsolete documentation, temporary debugging schemas, one-off experiments, and out-of-date master implementation roadmaps (V0 through V2.5) were discarded to eliminate historical noise.
- **Superseded OCR Architectures:** Extensive documentation detailing the micro-crop batching architecture (e.g., `BatchRunner`, `CropBatcher`) which was officially deprecated in the latest M4 refactor.
- **Obsolete UI/System Mappings:** Deprecated GUI control plane assumptions that no longer reflect the pure backend orchestration framework.
- **Duplicate Exception Specifications:** Repetitive low-level error class listings were condensed into the core Recovery Architecture section.

## 3. Conflicts Resolved
| Conflict | Resolution | Decision Rationale |
|---|---|---|
| **PaddleOCR Version** | 2.7.3 (Legacy API) over 3.x/PaddleX | PaddleX dynamic graphs caused unrecoverable WinError 127 crashes on Intel CPUs. The latest working runtime (2.7.3) is selected as canonical truth. |
| **M4 Execution Boundary** | Full-Page Matrix over Micro-Crop Batching | Micro-crops introduced unmanageable runtime instability. The architecture was officially shifted to full-page matrix OCR. |
| **Semantic Authority** | M5 over M3/M4 | Legacy notes occasionally blended spatial boundaries. The new truth strictly enforces that M3 owns geometry, M4 extracts raw text, and M5 assigns meaning. |

## 4. Deprecated Architectures
- **PaddleX Dynamic Graphs & PIR Executor:** Prohibited due to oneDNN compilation faults and Intel BLAS parallel conflicts.
- **Micro-Crop Batching (`crop_batcher.py`):** Eliminated due to performance overhead and system crashes during `np.array` serialization.
- **Classical CV Layout Analysis:** Superseded by the deep-learning DocTR `db_resnet50` backend in M3.

## 5. Final Architecture Decisions
- **Dependency Pinning:** The production stack is immutably pinned to `paddlepaddle==2.6.2`, `paddleocr==2.7.3`, and `numpy==1.26.4`.
- **Pre-Initialization Guards:** The orchestrator must globally bypass `modelscope` and pre-load PyTorch/Torchvision to prevent delayed DLL loading crashes in the pipeline.
- **Semantic Transition State:** M4 currently bypasses M3 spatial boundaries to generate its own detection boxes. The pipeline is considered functionally stable but semantically degraded (table/equation structure loss).
- **Future Direction (Hybrid Reconciliation):** M4 will maintain full-page execution for stability, but its raw output boxes must be mapped back into the canonical M3 layout regions using spatial IoU intersection to protect the integrity of the semantic hierarchy.

## 6. Confidence Assessment Per Module
| Module | Current Confidence | Assessment Notes |
|---|---|---|
| **M1 Ingestion** | HIGH | Very stable. Input constraints and normalization are solid. |
| **M2 Preprocessing** | HIGH | Core OpenCV operations are reliable and robust. |
| **M3 Layout Analysis** | MODERATE-HIGH | DocTR backend performs well, but bounding box accuracy on dense tables/forms could be improved. |
| **M4 OCR** | MODERATE | Execution stability is high, but the architectural transitional state (bypassing M3 bounds) lowers semantic fidelity. |
| **M5 Reconstruction** | MODERATE | Heuristics perform well for standard paragraphs but struggle heavily on flattened tables and equations due to M4's current architecture. |
| **M6 Export** | HIGH | Output serialization is atomic and reliable. |
| **M7 Orchestrator** | HIGH | State machine, isolation, and PyTorch environment locking have fully stabilized end-to-end runs. Memory/serialization performance requires future optimization. |
