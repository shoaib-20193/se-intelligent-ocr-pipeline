import os
import sys
from pathlib import Path

# 1. Dynamically locate your active virtual environment root directory
if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix):
    # Running inside a venv -> target root folder
    venv_path = Path(sys.prefix)
else:
    # Fallback to local directory if venv isn't active
    venv_path = Path(__file__).resolve().parents[3]

# ============================================================
# CRITICAL CPU BYPASS: Prevent paddlex from loading broken torch dlls
# ============================================================
from types import ModuleType
mock_modelscope = ModuleType("modelscope")
sys.modules["modelscope"] = mock_modelscope

# Pre-load PyTorch cleanly NOW so M3/DocTR never hits shm.dll cold
try:
    import torch
    import torchvision
    print("[INIT] PyTorch and Torchvision pre-loaded successfully for M3.")
except ImportError:
    print("[INIT] Warning: Could not pre-load PyTorch — M3 DocTR may fail.")
# ============================================================

# 2. Force PaddleX to download models into venv/.paddlex/ official folder structure
paddlex_cache_dir = venv_path / ".paddlex"
os.environ["PADDLE_PDX_CACHE_HOME"] = str(paddlex_cache_dir)

# 3. CPU instruction hotfixes - disable oneDNN/PIR to prevent Paddle 3.3.x crashes
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["CPU_NUM"] = "1"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_enable_onednn_operation_fuse"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"

# 4. Validate exact dependency versions before OCR initialization
try:
    import numpy as np
    import paddle
    import paddleocr
    if not np.__version__.startswith("1."):
        print(f"[ERROR] NumPy version mismatch. Expected 1.x, got {np.__version__}")
        sys.exit(1)
    if paddle.__version__ != "2.6.2":
        print(f"[ERROR] Paddle version mismatch. Expected 2.6.2, got {paddle.__version__}")
        sys.exit(1)
    if getattr(paddleocr, '__version__', None) != "2.7.3":
        print(f"[ERROR] PaddleOCR version mismatch. Expected 2.7.3, got {getattr(paddleocr, '__version__', None)}")
        sys.exit(1)
except ImportError as e:
    print(f"[ERROR] Failed to import required dependencies: {e}")
    sys.exit(1)

import argparse
import json
from src.pipeline.m7_orchestrator.interface import M7Orchestrator
from src.pipeline.m7_orchestrator.state.pipeline_state import PipelineState

def main():
    parser = argparse.ArgumentParser(description="Execute the V5 Document Processing Pipeline (M1 -> M4)")
    parser.add_argument("--input", type=str, required=True, help="Absolute path to input PDF or image")
    parser.add_argument("--profile", type=str, default="fast_draft", help="Profile config to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode overlays")
    
    args = parser.parse_args()
    
    print(f"Initializing M7 Orchestrator for {args.input}...")
    print(f"[INFO] PaddleX cache dir: {paddlex_cache_dir}")
    
    orchestrator = M7Orchestrator(
        config_flags={"profile_id": args.profile},
        debug_mode=args.debug
    )
    
    result = orchestrator.process_document(args.input)
    
    print(f"\nExecution Complete: {result.final_state.name}")
    print(f"Document ID: {result.document_id}")
    print(f"Total Time: {result.metrics.total_runtime_s:.2f}s")

    if result.final_state == PipelineState.COMPLETED:
        print("Success! Structured Document Generated.")
        if result.structured_document:
            print("\n================ M5 STRUCTURED OUTPUT ================\n")
            for page in result.structured_document.pages:
                print(f"--- PAGE {page.page_number} ---")
                if not page.tokens:
                    print("<No tokens found on this page>")
                for token in page.tokens:
                    print(f"[{token.block_type.upper()}] {token.text}")
                print()
            print("======================================================\n")
        sys.exit(0)
    else:
        print(f"Pipeline ended in state: {result.final_state.name}")
        print(f"Failures: {result.failure_summary}")
        sys.exit(1)


if __name__ == "__main__":
    main()
