"""
Optimized 2.7.3 Standalone Diagnostic & Run Script
Run: python scripts/debug_paddle_hang.py --input "path/to/your/document.pdf"
"""
import os
import sys
import time
import argparse
from pathlib import Path

# ============================================================
# CRITICAL CPU BYPASS: Prevent paddlex from loading broken torch dlls
# ============================================================
from types import ModuleType
mock_modelscope = ModuleType("modelscope")
sys.modules["modelscope"] = mock_modelscope
# ============================================================

# Force CPU thread constraint overrides to prevent system BLAS/OMP memory leaks
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

print("=" * 60)
print("DEBUG: PaddleOCR Hang Diagnosis")
print("=" * 60)
print(f"PADDLE_PDX_CACHE_HOME = {os.environ.get('PADDLE_PDX_CACHE_HOME', 'Not Set')}")
print(f"FLAGS_enable_pir_api  = {os.environ['FLAGS_enable_pir_api']}")
print(f"FLAGS_use_mkldnn      = {os.environ['FLAGS_use_mkldnn']}")
print()

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

def main():
    parser = argparse.ArgumentParser(description="Stable Standalone OCR Run Profile")
    parser.add_argument("--input", required=True, help="Path to input PDF or Image file")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: File not found -> {input_path}")
        sys.exit(1)

    print("=" * 60)
    print("STABLE ALIGNED OCR PASS RUNTIME (V2.7.3 Engine)")
    print("=" * 60)
    print(f"INPUT FILE            = {input_path}")
    print()

    # Step 1: Import backend math binaries
    print("[STEP 1] Importing paddle core...", flush=True)
    import paddle
    try:
        paddle.set_device('cpu')
        paddle.set_num_threads(1)
    except Exception:
        pass
    print(f"  Done | paddle version: {paddle.__version__}", flush=True)

    # Step 2: Import layout wrappers
    print("[STEP 2] Importing paddleocr modules...", flush=True)
    from paddleocr import PaddleOCR
    print(f"  Done", flush=True)

    # Step 4: Initialize engine instance targeting clean CPU paths
    print("[STEP 4] Spawning PaddleOCR engine layout...", flush=True)
    engine = PaddleOCR(lang="en", use_angle_cls=False, use_gpu=False, show_log=False)
    print(f"  Done", flush=True)

    # Step 5: Process targeted tracking document source
    print(f"[STEP 5] Executing inference engine...", flush=True)
    import numpy as np
    
    print("  [CHECKPOINT 5.1] Extracting page frames...", flush=True)
    if input_path.lower().endswith('.pdf'):
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(input_path)
            page = pdf[0]
            bitmap = page.render(scale=2)
            pil_img = bitmap.to_pil()
            test_img = np.array(pil_img, dtype=np.uint8)
        except Exception as pdf_err:
            print(f"  [ERROR] PDF handling structure fault: {pdf_err}")
            sys.exit(1)
    else:
        try:
            from PIL import Image
            test_img = np.array(Image.open(input_path).convert("RGB"), dtype=np.uint8)
        except Exception as img_err:
            print(f"  [ERROR] Image handling fault: {img_err}")
            sys.exit(1)

    print(f"  Input array constraints: {test_img.shape} | Data format: {test_img.dtype}", flush=True)
    print("  [CHECKPOINT 5.2] Deep-copying memory layout for native pass...", flush=True)
    working_img = np.ascontiguousarray(test_img.copy(), dtype=np.uint8)
    
    print("  [CHECKPOINT 5.3] Launching direct standalone matrix evaluation...", flush=True)
    t0 = time.time()
    try:
        # PaddleOCR 2.7.x processes an image matrix and returns a simple list structure
        # format: [ [ [ [x,y box coords], (text_string, accuracy_score) ] ] ]
        predictions = engine.ocr(working_img, cls=False)
        print(f"  [CHECKPOINT 5.4] PROCESSING FINISHED IN {time.time()-t0:.2f}s", flush=True)
        
        print("\n================ OCR OUTPUT ================\n")
        text_found = False
        
        if predictions:
            for page_data in predictions:
                if page_data is None:
                    continue
                for line in page_data:
                    # Safely extract bounding blocks from the nested matrix stream
                    if isinstance(line, list) and len(line) > 1:
                        text_box_info = line[1]
                        text = text_box_info[0]
                        confidence = text_box_info[1]
                        print(f"[{confidence:.2f}] -> {text}")
                        text_found = True
                        
        if not text_found:
            print("<No matching string fields could be extracted from page template>")
            
    except Exception as run_err:
        print(f"\n[CRITICAL ERROR] Core execution block failed: {run_err}", flush=True)
        
    print("\n============================================\n")

if __name__ == "__main__":
    main()
