"""
src/pipeline/m5_semantic/reconstructor.py
M5 Spatial Graph + Structure Reconstruction Engine.

Pipeline:
    1. Build SpatialGraph per page (GraphEngine)
    2. Compress graph nodes into DocumentBlocks (StructureBuilder)
    3. Convert blocks → SemanticSpatialTokens for M6 compatibility

After this stage, NO token-level fragmentation exists.
Every output unit = one human-level block (paragraph, table, heading, etc.)
"""
import logging
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m5_semantic.contracts import (
    StructuredDocument,
    StructuredPage,
    SemanticSpatialToken,
    BoundingBox
)
from src.pipeline.m5_semantic.graph.graph_engine import GraphEngine
from src.pipeline.m5_semantic.graph.structure_builder import StructureBuilder

logger = logging.getLogger(__name__)


class SemanticReconstructor:
    """
    M5 Document Reconstruction Engine.

    Two-phase architecture:
        Phase 1 (GraphEngine): Flat regions → spatial graph with edges, columns, order
        Phase 2 (StructureBuilder): Graph nodes → compressed DocumentBlocks

    Output: StructuredDocument where each token = one complete block, NOT a fragment.

    CRITICAL RULES:
        - M3 bbox is IMMUTABLE — passed through exactly (union for merged blocks)
        - Reading order comes from structure builder, not raw region order
        - Semantic labels come from structure classification, not text-only heuristics
        - No token-level fragmentation in output
    """

    def reconstruct(self, ocr_document: RecognizedDocument) -> StructuredDocument:
        structured_pages = []

        for page in ocr_document.pages:
            # ── Phase 1: Build spatial graph ──
            graph = GraphEngine.build_page_graph(page, page_width=float(page.page_width))

            if not graph.nodes:
                logger.warning(f"[M5] Page {page.page_number}: No graph nodes — empty page")
                structured_pages.append(StructuredPage(
                    page_number=page.page_number,
                    tokens=[],
                    page_width=float(page.page_width),
                    page_height=float(page.page_height),
                    spatial_graph=graph
                ))
                continue

            # ── Phase 2: Compress graph → DocumentBlocks ──
            doc_blocks = StructureBuilder.build_blocks(graph, page_width=float(page.page_width))

            if not doc_blocks:
                logger.warning(f"[M5] Page {page.page_number}: Structure builder produced 0 blocks")
                structured_pages.append(StructuredPage(
                    page_number=page.page_number,
                    tokens=[],
                    page_width=float(page.page_width),
                    page_height=float(page.page_height),
                    spatial_graph=graph
                ))
                continue

            # ── Phase 3: Convert DocumentBlocks → SemanticSpatialTokens for M6 ──
            tokens = []
            for block in sorted(doc_blocks, key=lambda b: b.reading_order):
                bbox = BoundingBox(
                    x_min=int(block.x),
                    y_min=int(block.y),
                    x_max=int(block.x + block.width),
                    y_max=int(block.y + block.height)
                )

                token = SemanticSpatialToken(
                    token_id=block.block_id,
                    text=block.text,
                    block_type=block.block_type,
                    bbox=bbox,
                    confidence=block.confidence,
                    reading_order=block.reading_order,
                    page_number=block.page_number,
                    source_region_id=block.children_node_ids[0] if block.children_node_ids else block.block_id,
                    column_id=block.column_id,
                    spatial_metadata={
                        "layout_role": block.layout_role,
                        "children_count": len(block.children_node_ids),
                        "children_node_ids": block.children_node_ids,
                        "num_columns_on_page": graph.num_columns,
                        "num_edges": len(graph.edges),
                        "is_table": block.block_type == "table",
                        "table_rows": block.table_rows if block.table_rows else None
                    }
                )
                tokens.append(token)

            logger.info(
                f"[M5] Page {page.page_number}: "
                f"{len(graph.nodes)} nodes → {len(doc_blocks)} blocks → {len(tokens)} output tokens | "
                f"{graph.num_columns} col(s), {len(graph.edges)} edges"
            )

            structured_pages.append(StructuredPage(
                page_number=page.page_number,
                tokens=tokens,
                page_width=float(page.page_width),
                page_height=float(page.page_height),
                spatial_graph=graph
            ))

        return StructuredDocument(
            source_document_id=ocr_document.source_document_id,
            pages=structured_pages,
            metadata=ocr_document.metadata
        )
