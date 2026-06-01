"""ProcessingRequest — agents.md §DATA_MODEL → ProcessingRequest"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class InputConstraints:
    max_pages: int = 50
    max_file_size_mb: int = 100


@dataclass
class ProcessingRequest:
    input_path: str
    profile_id: str
    output_formats: list[str] = field(default_factory=lambda: ["json"])
    constraints: InputConstraints = field(default_factory=InputConstraints)
