"""
tests/visual/test_ocr_pipeline.py
Integration validation for the M4 OCR Awakening Layer (V4).
"""
import pytest
import numpy as np
import copy
import cv2

from src.data_model.document import DocumentMetadata
from src.data_model.layout import LayoutDocument, LayoutPage, Region
from src.pipeline.m4_ocr.interface import M4OCREngine
from src.pipeline.m4_ocr.batching.memory_guard import MAX_BATCH_IMAGES
from src.utils.ocr_debug.ocr_overlay import generate_ocr_overlay

@pytest.fixture
def mock_clean_image():
    # A blank white image, 800x1100
    return np.ones((1100, 800, 3), dtype=np.uint8) * 255

@pytest.fixture
def mock_layout_doc():
    meta = DocumentMetadata("test.pdf", 1024, 1, (800, 1100))
    # Two regions
    r1 = Region(id="r1", bbox=(10, 10, 100, 40), polygon=None, confidence=0.9, type="text_block",
                crop_ref={"page_id": "p1", "bbox": [10, 10, 100, 40]},
                spatial_metadata={"reading_order": 1, "column_id": 0})
                
    r2 = Region(id="r2", bbox=(10, 50, 100, 80), polygon=None, confidence=0.9, type="text_block",
                crop_ref={"page_id": "p1", "bbox": [10, 50, 100, 80]},
                spatial_metadata={"reading_order": 0, "column_id": 0})
                
    page = LayoutPage(page_number=1, regions=[r1, r2])
    return LayoutDocument(document_id="test_doc", metadata=meta, pages=[page])

def test_reading_order_strictly_preserved(mock_layout_doc, mock_clean_image, monkeypatch):
    engine = M4OCREngine(confidence_threshold=0.0) # Accept all
    
    # Mock OCR inference to return deterministic strings
    def mock_recognize_batch(self, crops):
        return [("MOCKED_TEXT", 0.99) for _ in crops]
    monkeypatch.setattr("src.pipeline.m4_ocr.engines.paddle_engine.PaddleEngineWrapper.recognize_batch", mock_recognize_batch)
    
    # Run M4
    recognized_doc = engine.recognize_document(mock_layout_doc, {1: mock_clean_image})
    
    # Assert regions are strictly sorted by reading order (0, then 1)
    regions = recognized_doc.pages[0].regions
    assert len(regions) == 2
    assert regions[0].reading_order == 0
    assert regions[0].id == "r2" # r2 was reading order 0
    assert regions[1].reading_order == 1
    assert regions[1].id == "r1" # r1 was reading order 1

def test_spatial_metadata_preserved_losslessly(mock_layout_doc, mock_clean_image, monkeypatch):
    engine = M4OCREngine(confidence_threshold=0.0)
    
    def mock_recognize_batch(self, crops):
        return [("MOCKED_TEXT", 0.99) for _ in crops]
    monkeypatch.setattr("src.pipeline.m4_ocr.engines.paddle_engine.PaddleEngineWrapper.recognize_batch", mock_recognize_batch)
    
    # Inject a weird spatial metadata key to prove it passes through untouched
    mock_layout_doc.pages[0].regions[0].spatial_metadata["weird_m3_key"] = "test_val"
    
    recognized_doc = engine.recognize_document(mock_layout_doc, {1: mock_clean_image})
    
    for r in recognized_doc.pages[0].regions:
        if r.id == "r1":
            assert r.spatial_metadata.get("weird_m3_key") == "test_val"

def test_tiny_crop_rejection(mock_layout_doc, mock_clean_image, monkeypatch):
    # Make a tiny region (2x2 pixels) that should be rejected by ocr_normalizer
    tiny_r = Region(id="tiny", bbox=(10, 10, 12, 12), polygon=None, confidence=0.9, type="text_block",
                    crop_ref={"page_id": "p1", "bbox": [10, 10, 12, 12]},
                    spatial_metadata={"reading_order": 2})
                    
    mock_layout_doc.pages[0].regions.append(tiny_r)
    
    def mock_recognize_batch(self, crops):
        return [("MOCKED_TEXT", 0.99) for _ in crops]
    monkeypatch.setattr("src.pipeline.m4_ocr.engines.paddle_engine.PaddleEngineWrapper.recognize_batch", mock_recognize_batch)
    
    engine = M4OCREngine(confidence_threshold=0.0)
    recognized_doc = engine.recognize_document(mock_layout_doc, {1: mock_clean_image})
    
    # The tiny crop should be entirely dropped before OCR
    assert len(recognized_doc.pages[0].regions) == 2
    for r in recognized_doc.pages[0].regions:
        assert r.id != "tiny"

def test_batching_memory_guard_limits(mock_layout_doc, mock_clean_image):
    # Generate 100 regions (exceeding MAX_BATCH_IMAGES = 64)
    regions = []
    for i in range(100):
        r = Region(id=f"r{i}", bbox=(10, 10, 100, 40), polygon=None, confidence=0.9, type="text_block",
                   crop_ref={"page_id": "p1", "bbox": [10, 10, 100, 40]},
                   spatial_metadata={"reading_order": i})
        regions.append(r)
        
    mock_layout_doc.pages[0] = LayoutPage(page_number=1, regions=regions)
    
    from src.pipeline.m4_ocr.batching.crop_batcher import CropBatcher
    batcher = CropBatcher()
    
    batches = list(batcher.build_batches(mock_layout_doc.pages[0].regions, mock_clean_image))
    
    # 100 regions should split into at least 2 batches if MAX_BATCH_IMAGES is 64
    assert len(batches) >= 2
    
    # No batch should exceed MAX_BATCH_IMAGES
    for batch in batches:
        assert len(batch) <= MAX_BATCH_IMAGES

def test_debug_overlay_generation(mock_layout_doc, mock_clean_image, tmp_path, monkeypatch):
    # Monkeypatch DEBUG_DIR to a tmp path to avoid polluting real tree during tests
    import src.utils.ocr_debug.ocr_overlay
    src.utils.ocr_debug.ocr_overlay.DEBUG_DIR = tmp_path
    
    def mock_recognize_batch(self, crops):
        return [("MOCKED_TEXT", 0.99) for _ in crops]
    monkeypatch.setattr("src.pipeline.m4_ocr.engines.paddle_engine.PaddleEngineWrapper.recognize_batch", mock_recognize_batch)
    
    engine = M4OCREngine(confidence_threshold=0.0)
    recognized_doc = engine.recognize_document(mock_layout_doc, {1: mock_clean_image})
    
    generate_ocr_overlay(recognized_doc.pages[0], mock_clean_image, "test_doc")
    
    expected_file = tmp_path / "test_doc_page_1_ocr.jpg"
    assert expected_file.exists()
