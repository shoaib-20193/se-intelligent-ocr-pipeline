"""
Dataset Loader Utility — recursively discovers and sorts supported document files.
"""
from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

def collect_input_files(input_path: str) -> List[Path]:
    """
    Validates input path, detects file vs directory, and recursively
    collects all supported files with deterministic ordering.
    """
    path = Path(input_path).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")
        
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        else:
            raise ValueError(f"Unsupported file format: {path}")
            
    # Directory case
    collected = []
    for p in path.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            collected.append(p)
            
    return sorted(collected)
