"""StageTracker — per-stage per-page latency collection.
See agents.md §EXECUTION_ENGINE → Stage Logging, §MODULE_CONTRACTS → M7
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class StageMetric:
    stage: str
    latency_s: float
    pages_processed: int
    status: str = "ok"


class StageTracker:
    """
    Tracks execution order and latency for each pipeline stage.
    Used by M7 orchestrator to populate PipelineResult.stage_metrics.
    """

    def __init__(self) -> None:
        self._metrics: dict[str, StageMetric] = {}
        self._start_times: dict[str, float] = {}
        self._execution_order: list[str] = []

    def start(self, stage: str) -> None:
        """Mark stage start — call immediately before invoking a module."""
        self._start_times[stage] = time.monotonic()
        self._execution_order.append(stage)

    def end(self, stage: str, pages_processed: int = 0, status: str = "ok") -> float:
        """Mark stage end — returns elapsed seconds."""
        start = self._start_times.get(stage, time.monotonic())
        latency_s = round(time.monotonic() - start, 6)
        self._metrics[stage] = StageMetric(
            stage=stage,
            latency_s=latency_s,
            pages_processed=pages_processed,
            status=status,
        )
        return latency_s

    def get_report(self) -> dict:
        """Full structured report including execution order trace."""
        return {
            "execution_order": list(self._execution_order),
            "metrics": {
                name: {
                    "latency_s": m.latency_s,
                    "pages_processed": m.pages_processed,
                    "status": m.status,
                }
                for name, m in self._metrics.items()
            },
        }

    def to_pipeline_metrics(self) -> dict:
        """Returns dict matching PipelineResult.stage_metrics schema."""
        return {
            name: {
                "latency_s": m.latency_s,
                "pages_processed": m.pages_processed,
            }
            for name, m in self._metrics.items()
        }
