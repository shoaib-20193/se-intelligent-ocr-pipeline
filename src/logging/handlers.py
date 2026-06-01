"""Log output handlers — agents.md §EXECUTION_ENGINE → Stage Logging"""
from __future__ import annotations
import json
import threading
from dataclasses import asdict
from src.logging.schema import LogEntry


class ConsoleHandler:
    """Writes JSON-line log entries to stdout."""
    _lock = threading.Lock()

    def emit(self, entry: LogEntry) -> None:
        with self._lock:
            payload = asdict(entry)
            # Human-readable prefix for console
            prefix = f"[{entry.status.upper():7}] [{entry.stage:12}]"
            print(f"{prefix} {entry.message or json.dumps(payload)}", flush=True)


class FileHandler:
    """Writes JSON-line log entries to a rotating file."""
    _lock = threading.Lock()

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath

    def emit(self, entry: LogEntry) -> None:
        with self._lock:
            payload = asdict(entry)
            with open(self._filepath, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload) + "\n")


class GUIHandler:
    """Placeholder GUI log handler — emits to a callback (set by M8 at runtime)."""
    _callback = None

    @classmethod
    def set_callback(cls, fn) -> None:
        cls._callback = fn

    def emit(self, entry: LogEntry) -> None:
        if self._callback:
            self._callback(entry)
