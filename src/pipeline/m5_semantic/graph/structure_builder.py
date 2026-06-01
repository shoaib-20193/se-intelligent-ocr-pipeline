"""
src/pipeline/m5_semantic/graph/structure_builder.py
M5.5 — Document Reconstruction Engine.

Converts raw graph nodes into human-level structural blocks:
    - Paragraphs (merged vertical text flows)
    - Tables (row-major grid reconstruction from same_row edges)
    - Headings (full-width or ALL_CAPS short text)
    - Key-Value pairs (label: value patterns)
    - Lists (bullet/number-prefixed sequences)

This is the CRITICAL missing layer between "graph exists" and "document is correct".

RULE: After this stage, NO token-level structure may pass to M6.
      Every output is a compressed DocumentBlock.
"""
import logging
from typing import List, Dict, Set, Tuple, Optional
from src.pipeline.m5_semantic.graph.spatial_graph import (
    SpatialNode, SpatialGraph, SpatialRelation, SpatialEdge
)

logger = logging.getLogger(__name__)


class DocumentBlock:
    """
    A human-level structural unit. One block = one paragraph / one table / one heading.
    NOT a token. NOT a graph node. A reconstructed document element.
    """
    __slots__ = (
        'block_id', 'block_type', 'text', 'x', 'y', 'width', 'height',
        'page_number', 'reading_order', 'layout_role', 'children_node_ids',
        'confidence', 'column_id', 'table_rows'
    )

    def __init__(
        self,
        block_id: str,
        block_type: str,
        text: str,
        x: float, y: float, width: float, height: float,
        page_number: int,
        reading_order: int = 0,
        layout_role: str = "full_width",
        children_node_ids: List[str] = None,
        confidence: float = 0.0,
        column_id: int = -1,
        table_rows: List[List[str]] = None
    ):
        self.block_id = block_id
        self.block_type = block_type
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.page_number = page_number
        self.reading_order = reading_order
        self.layout_role = layout_role
        self.children_node_ids = children_node_ids or []
        self.confidence = confidence
        self.column_id = column_id
        self.table_rows = table_rows  # For tables: list of [cell1, cell2, ...]


class StructureBuilder:
    """
    Compresses a SpatialGraph into a list of DocumentBlocks.

    Pipeline:
        1. Detect headings (full-width or ALL_CAPS short text)
        2. Detect tables (same_row clusters with column spread)
        3. Detect key-value pairs (label: value patterns)
        4. Detect lists (bullet/number sequences)
        5. Merge remaining nodes into paragraphs
        6. Assign global reading order

    HARD CONSTRAINTS:
        - NEVER break M3 bounding boxes
        - bbox = union of children bboxes ONLY
        - NEVER output raw nodes after this stage
    """

    @staticmethod
    def build_blocks(graph: SpatialGraph, page_width: float = 800.0) -> List[DocumentBlock]:
        """Build DocumentBlocks from a SpatialGraph."""
        if not graph.nodes:
            return []

        visited: Set[str] = set()
        blocks: List[DocumentBlock] = []
        page_num = graph.page_number

        # Ensure index is built
        graph.build_index()

        # ── Pass 1: Headings (full-width or ALL_CAPS short) ──
        heading_blocks = StructureBuilder._detect_headings(graph, page_width, visited)
        blocks.extend(heading_blocks)

        # ── Pass 2: Tables (same_row clusters) ──
        table_blocks = StructureBuilder._detect_tables(graph, visited)
        blocks.extend(table_blocks)

        # ── Pass 3: Key-Value pairs ──
        kv_blocks = StructureBuilder._detect_key_value_pairs(graph, visited)
        blocks.extend(kv_blocks)

        # ── Pass 4: Lists (bullet/number prefixed sequences) ──
        list_blocks = StructureBuilder._detect_lists(graph, visited)
        blocks.extend(list_blocks)

        # ── Pass 5: Paragraphs (remaining unvisited nodes, merged by column proximity) ──
        para_blocks = StructureBuilder._detect_paragraphs(graph, visited)
        blocks.extend(para_blocks)

        # ── Pass 6: Global reading order ──
        StructureBuilder._assign_reading_order(blocks, page_width)

        logger.info(
            f"[M5.5] Page {page_num}: {len(blocks)} blocks "
            f"({sum(1 for b in blocks if b.block_type == 'heading')} headings, "
            f"{sum(1 for b in blocks if b.block_type == 'table')} tables, "
            f"{sum(1 for b in blocks if b.block_type == 'key_value_pair')} kv, "
            f"{sum(1 for b in blocks if b.block_type == 'list')} lists, "
            f"{sum(1 for b in blocks if b.block_type == 'paragraph')} paragraphs)"
        )

        return blocks

    # ────────────────────────────────────────────────────────────
    #  PASS 1: HEADING DETECTION
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_headings(
        graph: SpatialGraph, page_width: float, visited: Set[str]
    ) -> List[DocumentBlock]:
        blocks = []
        for node in graph.nodes:
            if node.node_id in visited:
                continue
            text = node.text.strip()
            if not text:
                continue

            is_full_width = node.width > 0.55 * page_width
            is_short = len(text) < 80
            is_upper = text.isupper() and len(text) > 2

            if (is_full_width and is_short) or (is_short and is_upper):
                visited.add(node.node_id)
                blocks.append(DocumentBlock(
                    block_id=f"heading-{node.node_id}",
                    block_type="heading",
                    text=text,
                    x=node.x, y=node.y,
                    width=node.width, height=node.height,
                    page_number=node.page_number,
                    layout_role="full_width" if is_full_width else _column_role(node),
                    children_node_ids=[node.node_id],
                    confidence=node.confidence,
                    column_id=node.column_id
                ))
        return blocks

    # ────────────────────────────────────────────────────────────
    #  PASS 2: TABLE DETECTION
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_tables(graph: SpatialGraph, visited: Set[str]) -> List[DocumentBlock]:
        """
        Detect tables by finding clusters of nodes connected by same_row edges.
        A table exists when ≥2 nodes share the same y-band AND span ≥2 x-columns.
        """
        blocks = []

        # Find all same_row clusters via BFS
        row_clusters = StructureBuilder._find_row_clusters(graph, visited)

        # A table = group of ≥2 rows that are vertically adjacent
        if not row_clusters:
            return blocks

        # Sort rows by y position
        row_clusters.sort(key=lambda row: min(n.y for n in row))

        # Group adjacent rows into tables
        table_groups = StructureBuilder._group_adjacent_rows(row_clusters)

        for tg_idx, table_rows in enumerate(table_groups):
            if len(table_rows) < 1:
                continue

            all_nodes = []
            row_texts = []
            for row in table_rows:
                # Sort cells left-to-right within the row
                sorted_row = sorted(row, key=lambda n: n.x)
                row_text = " | ".join(n.text.strip() for n in sorted_row)
                row_texts.append(row_text)
                all_nodes.extend(sorted_row)

            # Mark all as visited
            node_ids = []
            for n in all_nodes:
                visited.add(n.node_id)
                node_ids.append(n.node_id)

            # Union bbox
            x, y, w, h = _union_bbox(all_nodes)

            table_text = "\n".join(row_texts)
            raw_rows = [
                [n.text.strip() for n in sorted(row, key=lambda n: n.x)]
                for row in table_rows
            ]

            blocks.append(DocumentBlock(
                block_id=f"table-p{all_nodes[0].page_number}-{tg_idx}",
                block_type="table",
                text=table_text,
                x=x, y=y, width=w, height=h,
                page_number=all_nodes[0].page_number,
                layout_role="full_width",
                children_node_ids=node_ids,
                confidence=sum(n.confidence for n in all_nodes) / len(all_nodes),
                column_id=-1,
                table_rows=raw_rows
            ))

        return blocks

    @staticmethod
    def _find_row_clusters(
        graph: SpatialGraph, visited: Set[str]
    ) -> List[List[SpatialNode]]:
        """Find clusters of nodes that share same_row edges (≥2 nodes)."""
        clusters = []
        seen = set()

        for node in graph.nodes:
            if node.node_id in visited or node.node_id in seen:
                continue

            row_neighbors = graph.get_neighbors(node.node_id, SpatialRelation.SAME_ROW)
            # Only count unvisited neighbors
            row_neighbors = [n for n in row_neighbors if n.node_id not in visited]

            if len(row_neighbors) >= 1:
                # BFS to find full row cluster
                cluster = [node]
                queue = list(row_neighbors)
                cluster_seen = {node.node_id}
                while queue:
                    current = queue.pop(0)
                    if current.node_id in cluster_seen or current.node_id in visited:
                        continue
                    cluster_seen.add(current.node_id)
                    cluster.append(current)
                    further = graph.get_neighbors(current.node_id, SpatialRelation.SAME_ROW)
                    for f in further:
                        if f.node_id not in cluster_seen and f.node_id not in visited:
                            queue.append(f)

                if len(cluster) >= 2:
                    for n in cluster:
                        seen.add(n.node_id)
                    clusters.append(cluster)

        return clusters

    @staticmethod
    def _group_adjacent_rows(
        row_clusters: List[List[SpatialNode]], gap_threshold: float = 40.0
    ) -> List[List[List[SpatialNode]]]:
        """Group row clusters into tables based on vertical adjacency."""
        if not row_clusters:
            return []

        tables = [[row_clusters[0]]]

        for row in row_clusters[1:]:
            prev_row = tables[-1][-1]
            prev_y_max = max(n.y + n.height for n in prev_row)
            curr_y_min = min(n.y for n in row)

            if curr_y_min - prev_y_max < gap_threshold:
                tables[-1].append(row)
            else:
                tables.append([row])

        # Only keep groups with ≥2 rows (otherwise it's not really a table)
        return [t for t in tables if len(t) >= 2]

    # ────────────────────────────────────────────────────────────
    #  PASS 3: KEY-VALUE PAIR DETECTION
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_key_value_pairs(
        graph: SpatialGraph, visited: Set[str]
    ) -> List[DocumentBlock]:
        """Detect label:value patterns (e.g., 'Name: John Doe')."""
        blocks = []
        kv_group = []

        for node in sorted(graph.nodes, key=lambda n: (n.y, n.x)):
            if node.node_id in visited:
                continue
            text = node.text.strip()
            if not text:
                continue

            # Heuristic: contains ":" and is reasonably short
            if ":" in text and len(text.split()) <= 8:
                kv_group.append(node)
                visited.add(node.node_id)

        # Group adjacent KV pairs (within 30px vertical gap)
        if not kv_group:
            return blocks

        groups = [[kv_group[0]]]
        for node in kv_group[1:]:
            prev = groups[-1][-1]
            if node.y - (prev.y + prev.height) < 30:
                groups[-1].append(node)
            else:
                groups.append([node])

        for g_idx, group in enumerate(groups):
            if not group:
                continue
            merged_text = "\n".join(n.text.strip() for n in group)
            x, y, w, h = _union_bbox(group)
            node_ids = [n.node_id for n in group]

            blocks.append(DocumentBlock(
                block_id=f"kv-p{group[0].page_number}-{g_idx}",
                block_type="key_value_pair",
                text=merged_text,
                x=x, y=y, width=w, height=h,
                page_number=group[0].page_number,
                layout_role=_column_role(group[0]),
                children_node_ids=node_ids,
                confidence=sum(n.confidence for n in group) / len(group),
                column_id=group[0].column_id
            ))

        return blocks

    # ────────────────────────────────────────────────────────────
    #  PASS 4: LIST DETECTION
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_lists(graph: SpatialGraph, visited: Set[str]) -> List[DocumentBlock]:
        """Detect bullet/numbered list sequences."""
        blocks = []
        list_items = []

        for node in sorted(graph.nodes, key=lambda n: (n.column_id, n.y)):
            if node.node_id in visited:
                continue
            text = node.text.strip()
            if not text:
                continue

            first_word = text.split()[0] if text.split() else ""
            is_bullet = text.startswith(("•", "-", "*", "●", "○", "▪", "►"))
            is_numbered = first_word.rstrip(".):").isdigit()

            if is_bullet or is_numbered:
                list_items.append(node)
                visited.add(node.node_id)

        # Group adjacent list items
        if not list_items:
            return blocks

        groups = [[list_items[0]]]
        for node in list_items[1:]:
            prev = groups[-1][-1]
            same_col = node.column_id == prev.column_id
            close_y = node.y - (prev.y + prev.height) < 25
            if same_col and close_y:
                groups[-1].append(node)
            else:
                groups.append([node])

        for g_idx, group in enumerate(groups):
            merged_text = "\n".join(n.text.strip() for n in group)
            x, y, w, h = _union_bbox(group)
            node_ids = [n.node_id for n in group]

            blocks.append(DocumentBlock(
                block_id=f"list-p{group[0].page_number}-{g_idx}",
                block_type="list",
                text=merged_text,
                x=x, y=y, width=w, height=h,
                page_number=group[0].page_number,
                layout_role=_column_role(group[0]),
                children_node_ids=node_ids,
                confidence=sum(n.confidence for n in group) / len(group),
                column_id=group[0].column_id
            ))

        return blocks

    # ────────────────────────────────────────────────────────────
    #  PASS 5: PARAGRAPH DETECTION (catches everything remaining)
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_paragraphs(graph: SpatialGraph, visited: Set[str]) -> List[DocumentBlock]:
        """Merge remaining unvisited nodes into paragraphs by column + vertical proximity."""
        blocks = []
        remaining = [n for n in graph.nodes if n.node_id not in visited]

        if not remaining:
            return blocks

        # Sort by column then y
        remaining.sort(key=lambda n: (n.column_id, n.y, n.x))

        # Group by column + vertical proximity
        groups = [[remaining[0]]]
        visited.add(remaining[0].node_id)

        for node in remaining[1:]:
            if node.node_id in visited:
                continue
            visited.add(node.node_id)

            prev = groups[-1][-1]
            same_col = node.column_id == prev.column_id
            close_y = node.y - (prev.y + prev.height) < 30

            if same_col and close_y:
                groups[-1].append(node)
            else:
                groups.append([node])

        for g_idx, group in enumerate(groups):
            merged_text = " ".join(n.text.strip() for n in group)
            if not merged_text.strip():
                continue

            x, y, w, h = _union_bbox(group)
            node_ids = [n.node_id for n in group]

            blocks.append(DocumentBlock(
                block_id=f"para-p{group[0].page_number}-{g_idx}",
                block_type="paragraph",
                text=merged_text,
                x=x, y=y, width=w, height=h,
                page_number=group[0].page_number,
                layout_role=_column_role(group[0]),
                children_node_ids=node_ids,
                confidence=sum(n.confidence for n in group) / len(group),
                column_id=group[0].column_id
            ))

        return blocks

    # ────────────────────────────────────────────────────────────
    #  PASS 6: GLOBAL READING ORDER
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _assign_reading_order(blocks: List[DocumentBlock], page_width: float):
        """
        Assign final reading order:
            1. Full-width blocks first (sorted by y)
            2. Then column content (sorted by column → y → x)

        Within the same y-band, full-width headings come before column content.
        """
        BAND_TOLERANCE = 20.0

        # Separate full-width and column blocks
        full_width = [b for b in blocks if b.layout_role == "full_width"]
        column_blocks = [b for b in blocks if b.layout_role != "full_width"]

        # Build combined list with sort keys
        # (y_band, priority, column_id, y, x)
        entries = []
        for b in full_width:
            entries.append((b.y, 0, -1, b.y, b.x, b))
        for b in column_blocks:
            entries.append((b.y, 1, b.column_id, b.y, b.x, b))

        # Band-sort: group by y proximity, then priority + column
        entries.sort(key=lambda e: (e[0], e[1], e[2], e[3], e[4]))

        # Apply band-aware sorting
        if not entries:
            return

        bands = [[entries[0]]]
        for entry in entries[1:]:
            if abs(entry[0] - bands[-1][0][0]) <= BAND_TOLERANCE:
                bands[-1].append(entry)
            else:
                bands.append([entry])

        order = 0
        for band in bands:
            band.sort(key=lambda e: (e[1], e[2], e[3], e[4]))
            for entry in band:
                entry[5].reading_order = order
                order += 1


# ── Module-level helpers ──

def _union_bbox(nodes: List[SpatialNode]) -> Tuple[float, float, float, float]:
    """Compute union bounding box from M3 bboxes ONLY. Never invent coordinates."""
    x_min = min(n.x for n in nodes)
    y_min = min(n.y for n in nodes)
    x_max = max(n.x + n.width for n in nodes)
    y_max = max(n.y + n.height for n in nodes)
    return x_min, y_min, x_max - x_min, y_max - y_min


def _column_role(node: SpatialNode) -> str:
    """Determine layout role from column_id."""
    if node.column_id == 0:
        return "left_column"
    elif node.column_id == 1:
        return "right_column"
    elif node.column_id >= 2:
        return "multi_column"
    return "full_width"
