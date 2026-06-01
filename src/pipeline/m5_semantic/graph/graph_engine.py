"""
src/pipeline/m5_semantic/graph/graph_engine.py
The main orchestrator for the M5 Spatial Graph Engine.
Executes the 6-step pipeline: node construction → indexing → edges → columns → order → grouping.
"""
import logging
from typing import List, Optional
from src.data_model.ocr import RecognizedPage
from src.pipeline.m5_semantic.graph.spatial_graph import SpatialNode, SpatialGraph
from src.pipeline.m5_semantic.graph.edge_builder import EdgeBuilder
from src.pipeline.m5_semantic.graph.column_detector import ColumnDetector
from src.pipeline.m5_semantic.graph.reading_order_solver import ReadingOrderSolver

logger = logging.getLogger(__name__)


class GraphEngine:
    """
    Transforms a flat list of M3 regions + M4 text into a structured SpatialGraph.
    
    Pipeline:
        Step 1: Node construction (M3 region → SpatialNode with M4 text)
        Step 2: Spatial indexing (sort by y, x)
        Step 3: Edge construction (spatial relationships)
        Step 4: Column detection (x-coordinate clustering)
        Step 5: Reading order resolution (graph traversal)
        Step 6: Semantic grouping (merge adjacent same-type nodes)
    
    CRITICAL RULES:
        - M3 bbox is IMMUTABLE — never modified
        - Only groups, relates, and annotates
        - Every node gets at least 1 edge (no orphans)
    """

    @staticmethod
    def build_page_graph(page: RecognizedPage, page_width: float = 800.0) -> SpatialGraph:
        """
        Build a complete SpatialGraph for a single page.
        
        Args:
            page: RecognizedPage from M4 OCR output (contains M3 regions + text)
            page_width: Estimated page width for column detection
            
        Returns:
            Fully constructed SpatialGraph with edges, columns, and reading order
        """
        # ── Step 1: Node Construction ──
        nodes = GraphEngine._build_nodes(page)
        
        if not nodes:
            logger.warning(f"[GRAPH_ENGINE] Page {page.page_number}: No nodes constructed")
            return SpatialGraph(page_number=page.page_number)

        logger.info(f"[GRAPH_ENGINE] Page {page.page_number}: {len(nodes)} nodes constructed")

        # ── Step 2: Spatial Indexing (pre-sort) ──
        nodes.sort(key=lambda n: (n.y, n.x))

        # ── Step 3: Edge Construction ──
        edges = EdgeBuilder.build_edges(nodes)
        logger.info(f"[GRAPH_ENGINE] Page {page.page_number}: {len(edges)} edges constructed")

        # Build the graph
        graph = SpatialGraph(
            page_number=page.page_number,
            nodes=nodes,
            edges=edges
        )
        graph.build_index()

        # ── Step 4: Column Detection ──
        num_cols = ColumnDetector.detect_and_assign(nodes, page_width)
        logger.info(f"[GRAPH_ENGINE] Page {page.page_number}: {num_cols} column(s) detected")

        # ── Step 5: Reading Order Resolution ──
        ordered_nodes = ReadingOrderSolver.resolve(graph)
        logger.info(f"[GRAPH_ENGINE] Page {page.page_number}: Reading order resolved")

        # ── Step 6: Semantic Grouping ──
        # Merge adjacent nodes of the same type within the same column
        GraphEngine._apply_semantic_grouping(graph)

        return graph

    @staticmethod
    def _build_nodes(page: RecognizedPage) -> List[SpatialNode]:
        """
        Step 1: Create SpatialNode per M3 region.
        Groups OCR fragments by source_region_id and merges text.
        Bbox comes from PRIMARY fragment — NEVER recomputed.
        """
        # Group regions by M3 source_region_id
        region_groups = {}
        for region in page.regions:
            group_id = region.source_region_id or region.id
            if group_id not in region_groups:
                region_groups[group_id] = []
            region_groups[group_id].append(region)

        nodes = []
        for group_id, fragments in region_groups.items():
            # Sort fragments by reading_order for text merge
            sorted_frags = sorted(fragments, key=lambda r: (r.reading_order, r.bbox[1], r.bbox[0]))

            # Merge text
            merged_text = " ".join([r.text.strip() for r in sorted_frags if r.text.strip()])
            if not merged_text:
                continue

            # Bbox from PRIMARY fragment (M3 authoritative — IMMUTABLE)
            primary = sorted_frags[0]
            bbox = primary.bbox  # (x_min, y_min, x_max, y_max)

            # Average confidence
            avg_conf = sum(r.confidence for r in sorted_frags) / len(sorted_frags)

            node = SpatialNode(
                node_id=f"p{page.page_number}-{group_id}",
                text=merged_text,
                x=float(bbox[0]),
                y=float(bbox[1]),
                width=float(bbox[2] - bbox[0]),
                height=float(bbox[3] - bbox[1]),
                page_number=page.page_number,
                source_region_id=group_id,
                confidence=avg_conf
            )
            nodes.append(node)

        return nodes

    @staticmethod
    def _apply_semantic_grouping(graph: SpatialGraph):
        """
        Step 6: Apply semantic labels based on text content + spatial context.
        Uses the graph's column and adjacency information for smarter classification.
        """
        for node in graph.nodes:
            text = node.text.strip()
            if not text:
                node.semantic_label = "unknown"
                continue

            # Rule 1: Heading detection
            # Short + ALL CAPS, OR short + at the top of a column with content below
            is_short = len(text) < 80
            is_upper = text.isupper()
            has_below = len(graph.get_neighbors(node.node_id, SpatialRelation.BELOW)) > 0

            if is_short and is_upper:
                node.semantic_label = "heading"
                continue

            # Rule 2: Short text at top of column with content below → likely heading
            if is_short and has_below and node.y < 200:
                # Check if this is the first node in its column
                col_nodes = graph.get_nodes_in_column(node.column_id)
                if col_nodes and col_nodes[0].node_id == node.node_id:
                    node.semantic_label = "heading"
                    continue

            # Rule 3: List detection
            if text.startswith(("•", "-", "*", "●", "○", "▪")):
                node.semantic_label = "list"
                continue

            # Rule 4: Numbered list
            first_word = text.split()[0] if text.split() else ""
            if first_word.rstrip(".):").isdigit():
                node.semantic_label = "list"
                continue

            # Rule 5: Table row detection (nodes with many same_row neighbors)
            same_row_count = len(graph.get_neighbors(node.node_id, SpatialRelation.SAME_ROW))
            if same_row_count >= 2:
                node.semantic_label = "table"
                continue

            # Rule 6: Paragraph (enough words)
            if len(text.split()) > 5:
                node.semantic_label = "paragraph"
                continue

            # Rule 7: Short label-value pairs (e.g., "Name: John")
            if ":" in text and len(text.split()) <= 5:
                node.semantic_label = "paragraph"
                continue

            # Fallback
            node.semantic_label = "unknown"
