"""
src/pipeline/m5_semantic/graph/reading_order_solver.py
Resolves correct reading order by traversing the spatial graph.
Primary sort: column (left→right) → y position (top→bottom) → x position (left→right).
Ambiguity resolved via edge weights.
"""
from typing import List, Dict, Set
from src.pipeline.m5_semantic.graph.spatial_graph import SpatialNode, SpatialGraph, SpatialRelation


class ReadingOrderSolver:
    """
    Deterministic reading order resolver.
    Traverses the spatial graph using column-aware topological ordering.
    """

    @staticmethod
    def resolve(graph: SpatialGraph) -> List[SpatialNode]:
        """
        Assigns resolved_reading_order to every node in the graph.
        Returns nodes in final reading order.

        Algorithm:
        1. Group nodes by column_id
        2. Within each column, sort by y (top→bottom), break ties by x (left→right)
        3. Interleave columns left→right
        4. Handle special cases: headings that span columns go FIRST
        """
        if not graph.nodes:
            return []

        # Step 1: Identify full-width nodes (span multiple columns)
        # These are typically page-level headings and should come before column content
        num_columns = graph.num_columns
        full_width_nodes = []
        column_nodes: Dict[int, List[SpatialNode]] = {}

        if num_columns > 1:
            # Compute page x-range from all nodes
            page_x_min = min(n.x for n in graph.nodes)
            page_x_max = max(n.x_max for n in graph.nodes)
            page_span = page_x_max - page_x_min if page_x_max > page_x_min else 1.0

            for node in graph.nodes:
                node_span = node.width / page_span
                # If a node spans > 60% of page width in a multi-column layout,
                # it's a full-width element (heading, separator, etc.)
                if node_span > 0.6:
                    full_width_nodes.append(node)
                else:
                    col = node.column_id
                    if col not in column_nodes:
                        column_nodes[col] = []
                    column_nodes[col].append(node)
        else:
            # Single column: everything goes in column 0
            for node in graph.nodes:
                col = node.column_id
                if col not in column_nodes:
                    column_nodes[col] = []
                column_nodes[col].append(node)

        # Step 2: Sort full-width nodes by y position
        full_width_nodes.sort(key=lambda n: (n.y, n.x))

        # Step 3: Sort each column's nodes by y then x
        for col_id in column_nodes:
            column_nodes[col_id].sort(key=lambda n: (n.y, n.x))

        # Step 4: Build final order
        # Strategy: process nodes in y-band order
        # For each y-band, emit full-width nodes first, then column content left→right
        final_order = ReadingOrderSolver._interleave_with_full_width(
            full_width_nodes, column_nodes
        )

        # Step 5: Assign resolved_reading_order
        for idx, node in enumerate(final_order):
            node.resolved_reading_order = idx

        return final_order

    @staticmethod
    def _interleave_with_full_width(
        full_width: List[SpatialNode],
        columns: Dict[int, List[SpatialNode]]
    ) -> List[SpatialNode]:
        """
        Interleave full-width nodes with column content based on y position.
        Full-width nodes act as "section breaks" that reset column reading.
        """
        result = []

        # Merge all column nodes into a single sorted list with column-aware ordering
        # Process columns left→right (sorted by column_id)
        sorted_col_ids = sorted(columns.keys())

        # Build a combined list of (y_position, priority, node) for sorting
        # priority: 0 = full-width (comes first at same y), 1 = column content
        all_entries = []

        for node in full_width:
            all_entries.append((node.y, 0, -1, node))

        for col_id in sorted_col_ids:
            for node in columns[col_id]:
                all_entries.append((node.y, 1, col_id, node))

        # Sort by y position, then priority (full-width first), then column id
        all_entries.sort(key=lambda e: (e[0], e[1], e[2]))

        # Now we need to group column content by y-bands
        # Simple approach: just emit in sorted order, but ensure within same y-band
        # columns go left→right
        result = ReadingOrderSolver._band_sort(all_entries)

        return result

    @staticmethod
    def _band_sort(entries: list) -> List[SpatialNode]:
        """
        Groups entries into y-bands and sorts within each band.
        A band is defined as entries whose y values are within BAND_TOLERANCE of each other.
        """
        if not entries:
            return []

        BAND_TOLERANCE = 15.0  # pixels — entries within this y-range are "same row"

        bands = []
        current_band = [entries[0]]

        for entry in entries[1:]:
            if abs(entry[0] - current_band[0][0]) <= BAND_TOLERANCE:
                current_band.append(entry)
            else:
                bands.append(current_band)
                current_band = [entry]
        bands.append(current_band)

        # Within each band: full-width first (priority=0), then columns left→right
        result = []
        for band in bands:
            band.sort(key=lambda e: (e[1], e[2], e[0]))
            for entry in band:
                result.append(entry[3])  # the SpatialNode

        return result
