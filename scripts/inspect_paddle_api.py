import inspect

try:
    import paddleocr
    print(f"PaddleOCR version: {getattr(paddleocr, '__version__', 'unknown')}")
except Exception as e:
    print(f"Failed to import paddleocr: {e}")

try:
    from paddleocr import PaddleOCR
    print("\n--- PaddleOCR Signature ---")
    print(inspect.signature(PaddleOCR))
    
    print("\n--- PaddleOCR Dir ---")
    print([x for x in dir(PaddleOCR) if not x.startswith('_')])
    
    if hasattr(PaddleOCR, 'ocr'):
        print("\n--- PaddleOCR.ocr Signature ---")
        print(inspect.signature(PaddleOCR.ocr))
        
    if hasattr(PaddleOCR, 'predict'):
        print("\n--- PaddleOCR.predict Signature ---")
        print(inspect.signature(PaddleOCR.predict))
except Exception as e:
    print(f"Error inspecting PaddleOCR: {e}")
