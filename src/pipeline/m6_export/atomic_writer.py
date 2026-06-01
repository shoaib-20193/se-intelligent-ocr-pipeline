"""
atomic_writer — write to temp file then rename (no partial writes).
Mandatory for all M6 outputs. See agents.md §MODULE_CONTRACTS → M6
"""
from __future__ import annotations
import os
import tempfile


def atomic_write(content: str, target_path: str, encoding: str = "utf-8") -> None:
    """
    Write `content` to `target_path` atomically:
    1. Write to a sibling temp file
    2. os.replace() to target (atomic on POSIX; best-effort on Windows)

    Raises OSError if write or rename fails.
    """
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=target_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp_path, target_path)   # atomic on POSIX; Windows: best-effort
    except Exception:
        # Clean up temp file on failure; do not leave partial writes
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
