"""
M3LayoutEngine — full V3.2 spatial layout pipeline.
Orchestrates: detection → textline building → column detection →
              layout pattern → paragraph clustering → table candidates →
              region graph → reading order → compat normalization.
Strictly spatial/geometric only. No semantic inference at any stage.
"""
import logging
from src.data_model.preprocessed import PreprocessedDocument, ProcessedPage
from src.data_model.layout import LayoutDocument, LayoutPage, Region

logger = logging.getLogger(__name__)

# Confidence threshold: discard regions below this (§ALGO-CONF hard discard)
LAYOUT_CONFIDENCE_THRESHOLD = 0.5
LAYOUT_CONFIDENCE_WARNING   = 0.7


class M3LayoutEngine:
    """
    M3 Spatial Layout Intelligence Engine.
    Input:  PreprocessedDocument
    Output: LayoutDocument (Region objects sorted by reading order,
            enriched only with spatial_metadata)
    """

    def __init__(self, backend_name: str = "doctr", debug_viz: bool = False):
        self.backend_name = backend_name
        self.debug_viz = debug_viz
        self._backend = None

    # ------------------------------------------------------------------
    # Lazy backend initialisation
    # ------------------------------------------------------------------
    def _get_backend(self):
        if self._backend is None:
            if self.backend_name.lower() == "doctr":
                from .detection.doctr_detector import DocTRDetector
                self._backend = DocTRDetector()
                logger.info("[M3] DocTR backend initialised (lazy).")
            else:
                raise ValueError(f"[M3] Unknown backend: {self.backend_name!r}")
        return self._backend

    # ------------------------------------------------------------------
    # Public contract
    # ------------------------------------------------------------------
    def layout_analysis(self, preprocessed_doc: PreprocessedDocument) -> LayoutDocument:
        """
        Execute full M3 pipeline on a PreprocessedDocument.
        Returns a fully populated LayoutDocument.
        """
        backend = self._get_backend()
        doc_id  = preprocessed_doc.metadata.filename

        pages: list[LayoutPage] = []
        for page in preprocessed_doc.pages:
            layout_page = self._process_page(backend, page, doc_id)
            pages.append(layout_page)

        raw_doc = LayoutDocument(
            document_id=doc_id,
            metadata=preprocessed_doc.metadata,
            pages=pages,
            processing_metadata={"backend": self.backend_name, "version": "V3.2"},
        )

        # Final compat normalisation pass (validates V3.2 contracts, fills defaults)
        from .compat.compat_layer import normalize_layout_document
        final_doc = normalize_layout_document(raw_doc)

        logger.info(
            f"[M3] layout_analysis complete: {len(final_doc.pages)} page(s), "
            f"backend={self.backend_name}"
        )
        return final_doc

    # ------------------------------------------------------------------
    # Per-page pipeline
    # ------------------------------------------------------------------
    def _process_page(self, backend, page: ProcessedPage, doc_id: str) -> LayoutPage:
        image = page.clean_image
        if image is None:
            logger.warning(f"[M3] Page {page.page_number} has no image — returning empty LayoutPage.")
            return LayoutPage(page_number=page.page_number)

        h, w = image.shape[:2]
        pnum  = page.page_number
        logger.debug(f"[M3] Processing page {pnum} ({w}x{h})")

        # ── Stage 1: DocTR geometry extraction (word-level) ──────────
        word_regions: list[Region] = backend.detect_page(page, doc_id)
        logger.debug(f"[M3] Page {pnum}: {len(word_regions)} raw word regions from DocTR")

        # ── Stage 2: Confidence filtering (§ALGO-CONF hard discard) ─
        filtered: list[Region] = []
        for r in word_regions:
            if r.confidence < LAYOUT_CONFIDENCE_THRESHOLD:
                logger.debug(f"[M3] Discarding region {r.id} (conf={r.confidence:.3f} < {LAYOUT_CONFIDENCE_THRESHOLD})")
                continue
            if LAYOUT_CONFIDENCE_THRESHOLD <= r.confidence < LAYOUT_CONFIDENCE_WARNING:
                new_meta = dict(r.spatial_metadata)
                new_meta["low_confidence_flag"] = True
                r = Region(id=r.id, bbox=r.bbox, polygon=r.polygon,
                           confidence=r.confidence, type="text_block",
                           spatial_metadata=new_meta, crop_ref=r.crop_ref)
            filtered.append(r)
        logger.debug(f"[M3] Page {pnum}: {len(filtered)} regions after confidence filter")

        # ── Stage 2.5: Layout Collision Safety Engine (Force Field) ──
        from .layout_collision_safety import LayoutCollisionSafetyEngine
        normalized_regions = LayoutCollisionSafetyEngine.process(filtered, page_width=w, page_height=h)
        logger.debug(f"[M3] Page {pnum}: Applied collision safety to {len(normalized_regions)} regions")

        # ── Stage 3: Textline merging ────────────────────────────────
        from .spatial_analysis.textline_builder import build_textlines
        line_regions = build_textlines(normalized_regions, page_number=pnum, page_width=w)
        logger.debug(f"[M3] Page {pnum}: {len(line_regions)} line regions after textline merge")

        # ── Stage 4: Column detection ────────────────────────────────
        from .spatial_analysis.column_detector import detect_columns, assign_column_ids
        column_count, col_boundaries = detect_columns(line_regions, page_width=w, page_height=h)
        col_ids = assign_column_ids(line_regions, col_boundaries, page_width=w)

        # Attach column_id to spatial_metadata
        col_enriched: list[Region] = []
        for r, col_id in zip(line_regions, col_ids):
            new_meta = dict(r.spatial_metadata)
            new_meta["column_id"] = col_id
            col_enriched.append(Region(id=r.id, bbox=r.bbox, polygon=r.polygon,
                                       confidence=r.confidence, type="text_block",
                                       spatial_metadata=new_meta, crop_ref=r.crop_ref))

        # ── Stage 5: Layout pattern analysis ────────────────────────
        from .spatial_analysis.layout_pattern_analyzer import analyze_layout_pattern
        layout_type = analyze_layout_pattern(col_enriched, column_count, w, h)
        logger.debug(f"[M3] Page {pnum}: layout_type={layout_type}, column_count={column_count}")

        # ── Stage 6: Paragraph candidate clustering ──────────────────
        from .spatial_analysis.paragraph_cluster import cluster_paragraphs
        para_regions = cluster_paragraphs(col_enriched, page_width=w)

        # ── Stage 7: Table candidate detection ───────────────────────
        from .spatial_analysis.table_candidate_detector import detect_table_candidates
        table_regions = detect_table_candidates(para_regions, page_width=w, page_height=h)

        # ── Stage 8: Region adjacency graph ──────────────────────────
        from .spatial_analysis.region_graph import build_region_graph
        graph_regions = build_region_graph(table_regions, page_width=w, page_height=h)

        # ── Stage 9: Reading order resolution ────────────────────────
        from .spatial_analysis.reading_order import resolve_reading_order
        ordered_regions = resolve_reading_order(graph_regions)

        # ── Stage 10: Debug visualisation (optional) ─────────────────
        layout_page = LayoutPage(
            page_number=pnum,
            regions=ordered_regions,
            layout_type=layout_type,
            column_count=column_count,
            metadata={"page_width": w, "page_height": h},
        )

        if self.debug_viz:
            try:
                from src.utils.layout_viz import save_layout_debug
                save_layout_debug(image, layout_page, doc_id)
            except Exception as viz_err:
                logger.warning(f"[M3] Debug viz failed for page {pnum}: {viz_err}")

        return layout_page
