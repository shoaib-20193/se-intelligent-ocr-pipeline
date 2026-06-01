"""
M1 validator — agents.md §MODULE_CONTRACTS → M1 Processing Steps 1–4
"""
from __future__ import annotations
import os

ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
)


class ValidationError(Exception):
    """Raised when M1 rejects an input file."""


def validate_readable(path: str) -> None:
    if not os.path.isfile(path):
        raise ValidationError(f"File not found: '{path}'")
    try:
        with open(path, "rb") as f:
            f.read(4)
    except OSError as exc:
        raise ValidationError(f"Cannot read file: {exc}") from exc


def validate_extension(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported format '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(path: str, max_mb: float) -> None:
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValidationError(
            f"File {size_mb:.2f} MB exceeds limit of {max_mb} MB"
        )


def validate_page_count(page_count: int, max_pages: int) -> None:
    if page_count > max_pages:
        raise ValidationError(
            f"Page count {page_count} exceeds limit of {max_pages}"
        )
