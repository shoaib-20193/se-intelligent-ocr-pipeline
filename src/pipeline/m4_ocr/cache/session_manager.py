"""
src/pipeline/m4_ocr/cache/session_manager.py
Singleton cache for PaddleOCR to avoid repeatedly reloading the heavy model.
"""
import logging
import threading

logger = logging.getLogger(__name__)

from src.pipeline.m4_ocr.contracts.ocr_runtime_contracts import LegacyPaddleConfig

class PaddleOCRSessionManager:
    _instance = None
    _lock = threading.Lock()
    _engine = None
    _init_failed = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def get_engine(self, init_config: LegacyPaddleConfig):
        """
        Lazy-loads PaddleOCR 2.7.3 using stable legacy public API.
        """
        with self._lock:
            if self._init_failed:
                raise RuntimeError("PaddleOCR initialization previously failed.")

            if self._engine is None:
                logger.info("[M4] Initializing legacy PaddleOCR 2.7.3 engine.")

                try:
                    from paddleocr import PaddleOCR
                    import paddle

                    logger.info(f"[M4] PaddlePaddle version: {paddle.__version__}")

                    self._engine = PaddleOCR(
                        use_angle_cls=True,
                        lang='en',
                        use_gpu=False,
                        show_log=False
                    )
                    logger.info("[M4] PaddleOCR Session initialized successfully.")
                except Exception as e:
                    self._init_failed = True
                    logger.exception(f"[M4] PaddleOCR initialization failed: {e}")
                    raise
            return self._engine
