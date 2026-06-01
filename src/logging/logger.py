"""Structured pipeline logger — agents.md §EXECUTION_ENGINE → Stage Logging"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from src.logging.schema import LogEntry
from src.logging.handlers import ConsoleHandler


class PipelineLogger:
    """
    Singleton structured logger.
    All errors logged with: {timestamp, document_id, stage, page_number, error_type, message}
    No unhandled exception propagates to GUI layer — logger must never raise.
    See agents.md §ERROR_HANDLING_RULES
    """
    _instance: "PipelineLogger | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "PipelineLogger":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._handlers = [ConsoleHandler()]
                inst._handler_lock = threading.Lock()
                cls._instance = inst
        return cls._instance

    # ── Handler management ─────────────────────────────────────────────────

    def add_handler(self, handler) -> None:
        with self._handler_lock:
            self._handlers.append(handler)

    # ── Internal ────────────────────────────────────────────────────────────

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _emit(self, entry: LogEntry) -> None:
        with self._handler_lock:
            for handler in self._handlers:
                try:
                    handler.emit(entry)
                except Exception:
                    pass  # handler failure must never crash the pipeline

    # ── Public API ──────────────────────────────────────────────────────────

    def log_stage(
        self,
        document_id: str,
        stage: str,
        page_number: int,
        latency_s: float,
        status: str = "ok",
        message: str = "",
    ) -> None:
        self._emit(LogEntry(
            timestamp=self._now(),
            document_id=document_id,
            stage=stage,
            page_number=page_number,
            latency_s=round(latency_s, 4),
            status=status,
            message=message,
        ))

    def log_error(
        self,
        document_id: str,
        stage: str,
        page_number: int,
        error_type: str,
        error_message: str,
    ) -> None:
        self._emit(LogEntry(
            timestamp=self._now(),
            document_id=document_id,
            stage=stage,
            page_number=page_number,
            latency_s=0.0,
            status="error",
            message=f"[{error_type}] {error_message}",
        ))

    def info(self, message: str, document_id: str = "", stage: str = "M7") -> None:
        self.log_stage(document_id, stage, 0, 0.0, "ok", message)

    def warning(self, message: str, document_id: str = "", stage: str = "M7") -> None:
        self.log_stage(document_id, stage, 0, 0.0, "warning", message)

    def error(self, message: str, document_id: str = "", stage: str = "M7") -> None:
        self.log_stage(document_id, stage, 0, 0.0, "error", message)


# Module-level singleton — import this everywhere
logger = PipelineLogger()
