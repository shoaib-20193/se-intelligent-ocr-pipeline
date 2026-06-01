import os
import sys
import time
from pathlib import Path

# ============================================================
# CRITICAL CPU BYPASS: Prevent paddlex from loading broken torch dlls
# Pre-load PyTorch cleanly first to prevent torchvision::nms errors in M3
# ============================================================
from types import ModuleType
mock_modelscope = ModuleType("modelscope")
sys.modules["modelscope"] = mock_modelscope

try:
    import torch
    import torchvision
    print("[INIT] PyTorch and Torchvision pre-loaded successfully for M3.")
except ImportError:
    print("[INIT] Warning: Could not pre-load PyTorch.")
# ============================================================

# 1. Dynamically locate your active virtual environment root directory
if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix):
    venv_path = Path(sys.prefix)
else:
    venv_path = Path(__file__).resolve().parents[1]

# 2. Force PaddleX configuration references toward the target folder structure
paddlex_cache_dir = venv_path / ".paddlex"
os.environ["PADDLE_PDX_CACHE_HOME"] = str(paddlex_cache_dir)

# 3. CPU hardware locks to optimize the stable 2.7.3 / 2.6.2 matrix core engine
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

# Ensure the project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse

from src.data_model.request import ProcessingRequest
from src.data_model.configs import ProfileConfig
from src.pipeline.m7_orchestrator.adapters.m1_adapter import M1Adapter
from src.pipeline.m7_orchestrator.adapters.m2_adapter import M2Adapter
from src.pipeline.m7_orchestrator.adapters.m3_adapter import M3Adapter
from src.pipeline.m7_orchestrator.adapters.m4_adapter import M4Adapter

def main():
    parser = argparse.ArgumentParser(description="Standalone M4 Test Script")
    parser.add_argument("--input", required=True, help="Path to input PDF/Image")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: File not found -> {input_path}")
        sys.exit(1)

    print("=" * 60)
    print("ORCHESTRATION FRAMEWORK END-TO-END RUNTIME")
    print("=" * 60)
    print(f"[INFO] Active model directory trace: {paddlex_cache_dir}")
    print()

    try:
        # --- Stage M1 (Ingest) ---
        print(f"--- Running M1 (Ingest) for {input_path} ---")
        t0 = time.time()
        req = ProcessingRequest(input_path=input_path, profile_id="fast_draft")
        m1 = M1Adapter()
        doc = m1.execute(req)
        print(f"  M1 completed in {time.time()-t0:.2f}s")

        # --- Stage M2 (Preprocess) ---
        print(f"--- Running M2 (Preprocess) ---")
        t0 = time.time()
        m2 = M2Adapter()
        profile = ProfileConfig(profile_id="fast_draft")
        pre_doc = m2.execute(doc, profile)
        
        # Pull out page arrays for the processing adapters
        clean_images = {p.page_number: p.clean_image for p in pre_doc.pages if p.clean_image is not None}
        print(f"  M2 completed in {time.time()-t0:.2f}s | Unpacked {len(clean_images)} images.")

        # --- Stage M3 (Layout Analysis) ---
        print(f"--- Running M3 (Layout via DocTR) ---")
        t0 = time.time()
        m3 = M3Adapter()
        layout_doc = m3.execute(pre_doc)
        print(f"  M3 completed in {time.time()-t0:.2f}s")

        # --- Stage M4 (Text Extraction Engine) ---
        print(f"--- Running M4 (Stable 2.7.3 Standalone OCR) ---")
        t0 = time.time()
        m4 = M4Adapter(confidence_threshold=0.5)
        rec_doc = m4.execute(layout_doc, clean_images)
        print(f"  M4 completed in {time.time()-t0:.2f}s")

        # --- Print Extraction Output Data ---
        print("\n================ OCR OUTPUT ================\n")
        text_found = False
        for page in rec_doc.pages:
            print(f"--- PAGE {page.page_number} ---")
            if not page.raw_text or not page.raw_text.strip():
                print("<No text found on this page>")
            else:
                print(page.raw_text)
                text_found = True
            print("\n")
        print("============================================\n")

        if not text_found:
            print("[WARNING] Pipeline completed but final text storage blocks returned empty.")

    except Exception as e:
        print(f"\n[ERROR] Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("ALL RUNTIME PIPELINES EXITED CLEANLY")
    print("=" * 60)

if __name__ == "__main__":
    main()
