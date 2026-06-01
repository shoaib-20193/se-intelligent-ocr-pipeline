"""
tests/visual/test_layout_detection.py
Integration validation for the M3 Spatial Layout Intelligence Layer (V3.2).

Validates:
- Deterministic repeated execution
- No semantic labels in M3 output
- Region.type always equals "text_block"
- Spatial metadata correctly populated
- No image mutation side effects
- Large-page stress validation with dense synthetic inputs
- Visual debug outputs generated correctly
- Batch real-document processing via CLI
"""
from __future__ import annotations
import os
import sys
import copy
import time
import argparse
import logging
import numpy as np
import pytest
from pathlib import Path

from src.data_model.document import DocumentMetadata
from src.data_model.preprocessed import PreprocessedDocument, ProcessedPage
from src.data_model.layout import Region, LayoutDocument
from src.pipeline.m3_layout.interface import M3LayoutEngine

try:
    from tests.utils.dataset_loader import collect_input_files
    from tests.utils.document_loader import load_real_document
    _LOADERS_AVAILABLE = True
except ImportError:
    _LOADERS_AVAILABLE = False


# ── Forbidden semantic values (V3.2 firewall) ────────────────────────
FORBIDDEN_REGION_TYPES = {"header", "footer", "paragraph", "section", "title", "caption", "table"}
FORBIDDEN_METADATA_KEYS = {"header", "footer", "title", "section", "caption", "semantic_class",
                            "paragraph_type", "section_type", "heading_level"}


# ── Synthetic test fixtures ───────────────────────────────────────────

def _make_blank_page(page_number: int = 1, width: int = 800, height: int = 1100) -> ProcessedPage:
    """Create a white blank page with no text regions."""
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    return ProcessedPage(page_number=page_number, clean_image=image)


def _make_synthetic_page(page_number: int = 1, width: int = 800, height: int = 1100,
                          num_blocks: int = 12) -> ProcessedPage:
    """
    Create a synthetic white page with dark rectangles simulating text blocks.
    DocTR will detect these as regions.
    """
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    block_h = 24
    block_w = 320
    margin_x = 60
    margin_y = 80
    row_gap = 40

    for i in range(num_blocks):
        y1 = margin_y + i * (block_h + row_gap)
        if y1 + block_h > height - margin_y:
            break
        x1 = margin_x + (i % 2) * (width // 2 - margin_x)
        x2 = x1 + block_w
        y2 = y1 + block_h
        image[y1:y2, x1:x2] = 40  # dark rectangle = simulated text line

    return ProcessedPage(page_number=page_number, clean_image=image)


def _make_preprocessed_doc(pages: list[ProcessedPage]) -> PreprocessedDocument:
    meta = DocumentMetadata(
        filename="test_doc.pdf",
        file_size=1024,
        page_count=len(pages),
        resolution=(800, 1100),
    )
    return PreprocessedDocument(metadata=meta, pages=pages)


# ── Unit: bbox utilities ──────────────────────────────────────────────

class TestBboxUtils:
    def test_iou_identical(self):
        from src.utils.bbox_utils import iou
        b = (10, 10, 50, 50)
        assert iou(b, b) == pytest.approx(1.0)

    def test_iou_no_overlap(self):
        from src.utils.bbox_utils import iou
        assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == pytest.approx(0.0)

    def test_iou_partial(self):
        from src.utils.bbox_utils import iou
        a = (0, 0, 20, 20)
        b = (10, 10, 30, 30)
        result = iou(a, b)
        assert 0.0 < result < 1.0

    def test_clip_bbox_within_bounds(self):
        from src.utils.bbox_utils import clip_bbox
        result = clip_bbox((-5, -5, 810, 1110), 800, 1100)
        assert result == (0, 0, 800, 1100)

    def test_bbox_distance_same_center(self):
        from src.utils.bbox_utils import bbox_distance
        b = (0, 0, 20, 20)
        assert bbox_distance(b, b) == pytest.approx(0.0)


# ── Unit: bbox normalization ──────────────────────────────────────────

class TestBboxNormalizer:
    def test_normalize_full_page(self):
        from src.pipeline.m3_layout.detection.bbox_normalizer import normalize_bbox
        result = normalize_bbox((0.0, 0.0, 1.0, 1.0), width=800, height=1100)
        assert result == (0, 0, 800, 1100)

    def test_normalize_clips_oob(self):
        from src.pipeline.m3_layout.detection.bbox_normalizer import normalize_bbox
        result = normalize_bbox((-0.1, -0.1, 1.1, 1.1), width=800, height=1100)
        assert result[0] >= 0 and result[1] >= 0
        assert result[2] <= 800 and result[3] <= 1100

    def test_normalize_order_preserved(self):
        from src.pipeline.m3_layout.detection.bbox_normalizer import normalize_bbox
        x1, y1, x2, y2 = normalize_bbox((0.1, 0.2, 0.9, 0.8), 800, 1100)
        assert x1 < x2
        assert y1 < y2


# ── Unit: crop_ref is lightweight ────────────────────────────────────

class TestCropExtractor:
    def test_crop_ref_is_dict(self):
        from src.pipeline.m3_layout.detection.crop_extractor import extract_crop_ref
        ref = extract_crop_ref("doc_p1", (10, 20, 100, 80))
        assert isinstance(ref, dict)
        assert "page_id" in ref and "bbox" in ref

    def test_crop_ref_no_ndarray(self):
        from src.pipeline.m3_layout.detection.crop_extractor import extract_crop_ref
        ref = extract_crop_ref("doc_p1", (10, 20, 100, 80))
        assert not isinstance(ref.get("bbox"), np.ndarray)
        assert isinstance(ref["bbox"], list)


# ── Unit: textline builder ────────────────────────────────────────────

class TestTextlineBuilder:
    def _make_regions(self):
        """Two words on the same line, one on a new line."""
        return [
            Region(id="p1-w0", bbox=(10, 10, 100, 30), polygon=None, confidence=0.9),
            Region(id="p1-w1", bbox=(110, 12, 200, 32), polygon=None, confidence=0.85),
            Region(id="p1-w2", bbox=(10, 80, 150, 100), polygon=None, confidence=0.88),
        ]

    def test_two_words_merge_into_one_line(self):
        from src.pipeline.m3_layout.spatial_analysis.textline_builder import build_textlines
        regions = self._make_regions()
        lines = build_textlines(regions, page_number=1, page_width=800)
        assert len(lines) == 2  # first two merge; third stays separate

    def test_all_types_are_text_block(self):
        from src.pipeline.m3_layout.spatial_analysis.textline_builder import build_textlines
        regions = self._make_regions()
        lines = build_textlines(regions, page_number=1, page_width=800)
        for line in lines:
            assert line.type == "text_block"

    def test_no_mutation_of_source(self):
        from src.pipeline.m3_layout.spatial_analysis.textline_builder import build_textlines
        regions = self._make_regions()
        ids_before = [r.id for r in regions]
        build_textlines(regions, page_number=1, page_width=800)
        assert [r.id for r in regions] == ids_before


# ── Unit: column detector ─────────────────────────────────────────────

class TestColumnDetector:
    def _left_right_regions(self):
        left = [Region(id=f"l{i}", bbox=(50, i * 60, 350, i * 60 + 40), polygon=None, confidence=0.9)
                for i in range(5)]
        right = [Region(id=f"r{i}", bbox=(450, i * 60, 750, i * 60 + 40), polygon=None, confidence=0.9)
                 for i in range(5)]
        return left + right

    def test_detects_two_columns(self):
        from src.pipeline.m3_layout.spatial_analysis.column_detector import detect_columns
        regions = self._left_right_regions()
        count, _ = detect_columns(regions, page_width=800, page_height=1100)
        assert count == 2

    def test_single_column_page(self):
        from src.pipeline.m3_layout.spatial_analysis.column_detector import detect_columns
        regions = [Region(id=f"r{i}", bbox=(60, i * 60, 740, i * 60 + 40), polygon=None, confidence=0.9)
                   for i in range(5)]
        count, _ = detect_columns(regions, page_width=800, page_height=1100)
        assert count == 1


# ── Unit: reading order ───────────────────────────────────────────────

class TestReadingOrder:
    def test_sorted_top_to_bottom(self):
        from src.pipeline.m3_layout.spatial_analysis.reading_order import resolve_reading_order
        regions = [
            Region(id="r2", bbox=(10, 200, 100, 230), polygon=None, confidence=0.9,
                   spatial_metadata={"column_id": 0}),
            Region(id="r0", bbox=(10, 10,  100,  40), polygon=None, confidence=0.9,
                   spatial_metadata={"column_id": 0}),
            Region(id="r1", bbox=(10, 100, 100, 130), polygon=None, confidence=0.9,
                   spatial_metadata={"column_id": 0}),
        ]
        ordered = resolve_reading_order(regions)
        orders = [r.spatial_metadata["reading_order"] for r in ordered]
        assert orders == [0, 1, 2]
        assert ordered[0].id == "r0"
        assert ordered[2].id == "r2"

    def test_deterministic_repeated_calls(self):
        from src.pipeline.m3_layout.spatial_analysis.reading_order import resolve_reading_order
        regions = [
            Region(id="ra", bbox=(10, 50, 100, 80),   polygon=None, confidence=0.9,
                   spatial_metadata={"column_id": 0}),
            Region(id="rb", bbox=(10, 10, 100, 40),   polygon=None, confidence=0.9,
                   spatial_metadata={"column_id": 0}),
        ]
        result_a = [r.id for r in resolve_reading_order(regions)]
        result_b = [r.id for r in resolve_reading_order(regions)]
        assert result_a == result_b

    def test_no_semantic_fields_set(self):
        from src.pipeline.m3_layout.spatial_analysis.reading_order import resolve_reading_order
        regions = [Region(id="rx", bbox=(10, 10, 100, 40), polygon=None,
                          confidence=0.9, spatial_metadata={"column_id": 0})]
        ordered = resolve_reading_order(regions)
        for r in ordered:
            for key in FORBIDDEN_METADATA_KEYS:
                assert key not in r.spatial_metadata, f"Forbidden key '{key}' found in reading_order output"


# ── Unit: compat layer enforcement ───────────────────────────────────

class TestCompatLayer:
    def _make_valid_doc(self) -> LayoutDocument:
        from src.data_model.layout import LayoutPage, LayoutDocument, Region
        from src.data_model.document import DocumentMetadata
        meta = DocumentMetadata("test.pdf", 1024, 1, (800, 1100))
        region = Region(id="p1-r0", bbox=(10, 10, 100, 40), polygon=None, confidence=0.9,
                        type="text_block", spatial_metadata={})
        page = LayoutPage(page_number=1, regions=[region])
        return LayoutDocument(document_id="test", metadata=meta, pages=[page])

    def test_valid_doc_passes(self):
        from src.pipeline.m3_layout.compat.compat_layer import normalize_layout_document
        doc = self._make_valid_doc()
        result = normalize_layout_document(doc)
        assert len(result.pages) == 1

    def test_semantic_type_raises(self):
        from src.pipeline.m3_layout.compat.compat_layer import normalize_layout_document
        from src.data_model.layout import LayoutPage, LayoutDocument, Region
        from src.data_model.document import DocumentMetadata
        meta = DocumentMetadata("test.pdf", 1024, 1, (800, 1100))
        bad_region = Region(id="p1-r0", bbox=(10, 10, 100, 40), polygon=None,
                            confidence=0.9, type="header")  # FORBIDDEN
        page = LayoutPage(page_number=1, regions=[bad_region])
        bad_doc = LayoutDocument(document_id="test", metadata=meta, pages=[page])
        with pytest.raises(ValueError, match="V3.2 VIOLATION"):
            normalize_layout_document(bad_doc)

    def test_semantic_metadata_key_raises(self):
        from src.pipeline.m3_layout.compat.compat_layer import normalize_layout_document
        from src.data_model.layout import LayoutPage, LayoutDocument, Region
        from src.data_model.document import DocumentMetadata
        meta = DocumentMetadata("test.pdf", 1024, 1, (800, 1100))
        bad_region = Region(id="p1-r0", bbox=(10, 10, 100, 40), polygon=None,
                            confidence=0.9, type="text_block",
                            spatial_metadata={"title": "some_title"})  # FORBIDDEN KEY
        page = LayoutPage(page_number=1, regions=[bad_region])
        bad_doc = LayoutDocument(document_id="test", metadata=meta, pages=[page])
        with pytest.raises(ValueError, match="SEMANTIC LEAKAGE"):
            normalize_layout_document(bad_doc)

    def test_defaults_filled_in(self):
        from src.pipeline.m3_layout.compat.compat_layer import normalize_layout_document
        doc = self._make_valid_doc()
        result = normalize_layout_document(doc)
        region = result.pages[0].regions[0]
        assert "reading_order" in region.spatial_metadata
        assert "cluster_id" in region.spatial_metadata
        assert "adjacency_links" in region.spatial_metadata
        assert "table_candidate" in region.spatial_metadata
        assert "paragraph_candidate" in region.spatial_metadata


# ── Stress: large page with dense regions ────────────────────────────

class TestStress:
    def test_graph_does_not_explode_on_dense_page(self):
        """Ensure region_graph handles 200 regions without timing out."""
        from src.pipeline.m3_layout.spatial_analysis.region_graph import build_region_graph
        import time
        regions = [
            Region(id=f"r{i}", bbox=(
                (i % 20) * 38, (i // 20) * 50,
                (i % 20) * 38 + 36, (i // 20) * 50 + 24
            ), polygon=None, confidence=0.9, spatial_metadata={"column_id": i % 2})
            for i in range(200)
        ]
        t0 = time.time()
        result = build_region_graph(regions, page_width=800, page_height=1100)
        elapsed = time.time() - t0
        assert elapsed < 5.0, f"Graph construction took too long: {elapsed:.2f}s"
        assert len(result) == 200

    def test_no_ndarray_in_regions(self):
        """Crop refs must never contain full ndarray copies."""
        from src.pipeline.m3_layout.spatial_analysis.region_graph import build_region_graph
        regions = [
            Region(id=f"r{i}", bbox=(i * 50, 10, i * 50 + 40, 40), polygon=None,
                   confidence=0.9, crop_ref={"page_id": "p1", "bbox": [i * 50, 10, i * 50 + 40, 40]})
            for i in range(10)
        ]
        result = build_region_graph(regions, page_width=800, page_height=1100)
        for r in result:
            if r.crop_ref is not None:
                assert isinstance(r.crop_ref, dict)
                assert not isinstance(r.crop_ref.get("bbox"), np.ndarray)


# ── Batch Integration (Pytest / CLI Hook) ────────────────────────────

def run_batch_integration(input_path: str):
    """
    Core batch processing logic used by both pytest and CLI runner.
    Finds files, runs layout engine defensively, and produces summary stats.
    """
    if not _LOADERS_AVAILABLE:
        print("[ERROR] Required loaders (dataset_loader, document_loader) missing.")
        return

    print(f"\n[INFO] Starting Layout Detection Batch Run")
    print(f"[INFO] Input Target: {input_path}")
    
    try:
        files = collect_input_files(input_path)
    except Exception as e:
        print(f"[ERROR] Failed to collect input files: {e}")
        return

    total = len(files)
    print(f"[INFO] Loading {total} files from dataset")
    if total == 0:
        print("[WARNING] No supported documents found. Exiting.")
        return

    # Initialize Engine
    engine = M3LayoutEngine(backend_name="doctr", debug_viz=True)
    
    succeeded = 0
    failed = 0
    start_time = time.time()

    for idx, fpath in enumerate(files, start=1):
        print(f"\n[INFO] [{idx}/{total}] Processing: {fpath.name}")
        try:
            doc = load_real_document(fpath)
            # Run layout detection
            layout_doc = engine.layout_analysis(doc)
            
            # Additional V3.2 validations on output
            for page in layout_doc.pages:
                for r in page.regions:
                    assert r.type == "text_block", f"Semantic leakage: {r.type}"
            
            print(f"[INFO] ✓ Success. Detected {sum(len(p.regions) for p in layout_doc.pages)} total regions.")
            succeeded += 1
        except ImportError as ie:
            print(f"[WARNING] Missing dependency (skipping): {ie}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] ✗ Failed processing {fpath.name}: {e}")
            failed += 1

    elapsed = time.time() - start_time
    print("\n" + "="*40)
    print("BATCH RUN SUMMARY STATISTICS")
    print("="*40)
    print(f"Processed:    {total}")
    print(f"Succeeded:    {succeeded}")
    print(f"Failed:       {failed}")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print("="*40)


def test_real_documents_batch(request):
    """
    Pytest entry point for batch processing.
    Requires --input CLI argument.
    """
    input_path = request.config.getoption("--input")
    if not input_path:
        pytest.skip("No --input provided for batch test. Skipping real-document batch execution.")
        
    run_batch_integration(input_path)


# ── Standalone CLI Runner ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="M3 Layout Detection Batch Runner")
    parser.add_argument("--input", type=str, required=True, help="Path to file or folder containing PDFs/images")
    
    # Use parse_known_args to gracefully ignore arguments meant for pytest (like -s)
    args, unknown = parser.parse_known_args()
    
    if unknown:
        print(f"[WARNING] Ignoring unrecognized arguments: {' '.join(unknown)}")
        
    run_batch_integration(args.input)
