"""
src/pipeline/m4_ocr/batching/memory_guard.py
Ensures OCR batches do not exceed memory constraints using dynamic limits.
"""

MAX_BATCH_IMAGES = 64
MAX_BATCH_PIXELS = 12000000  # 12 MP

class BatchMemoryGuard:
    def __init__(self):
        self.current_images = 0
        self.current_pixels = 0

    def can_add(self, width: int, height: int) -> bool:
        """
        Returns True if adding this image stays within limits.
        """
        area = width * height
        if self.current_images + 1 > MAX_BATCH_IMAGES:
            return False
        if self.current_pixels + area > MAX_BATCH_PIXELS:
            return False
        return True

    def add(self, width: int, height: int):
        self.current_images += 1
        self.current_pixels += (width * height)

    def reset(self):
        self.current_images = 0
        self.current_pixels = 0
