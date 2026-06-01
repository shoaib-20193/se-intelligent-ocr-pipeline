"""
main.py — Application entry point
V1: Real file validation, real JSON export, typed pipeline context.
Usage: python main.py [path_to_file]
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_model.request import ProcessingRequest, InputConstraints
from src.engine.orchestrator import run

# ── Minimal valid 1-page PDF (no library needed) ─────────────────────────────
_MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f\r
0000000009 00000 n\r
0000000052 00000 n\r
0000000101 00000 n\r
trailer<</Size 4/Root 1 0 R>>
startxref
160
%%EOF"""


def _ensure_sample_file(path: str) -> None:
    """Create a minimal valid PDF fixture if the sample doesn't already exist."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if not os.path.isfile(path):
        with open(path, "wb") as f:
            f.write(_MINIMAL_PDF)
        print(f"  [INFO] Created sample file: {path}")


def main() -> None:
    sample_path = sys.argv[1] if len(sys.argv) > 1 else "data/input/sample.pdf"
    _ensure_sample_file(sample_path)

    print("=" * 60)
    print("  Intelligent OCR Pipeline — V1 Data Flow Validation")
    print("=" * 60)
    print(f"  Input      : {sample_path}")
    print(f"  Profile    : fast_draft")
    print()

    request = ProcessingRequest(
        input_path=sample_path,
        profile_id="fast_draft",
        output_formats=["json"],
        constraints=InputConstraints(max_pages=50, max_file_size_mb=100),
    )

    result = run(request)

    print()
    print("=" * 60)
    print("  PIPELINE RESULT")
    print("=" * 60)
    print(f"  Document ID  : {result.document_id}")
    print(f"  Status       : {result.status.upper()}")
    print(f"  Total time   : {result.processing_time}s")
    print(f"  Stage metrics:")
    print(json.dumps(result.stage_metrics, indent=4))
    print("=" * 60)

    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
