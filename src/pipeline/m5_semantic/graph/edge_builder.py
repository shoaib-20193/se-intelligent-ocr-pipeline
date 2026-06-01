"""
src/pipeline/m5_semantic/graph/edge_builder.py
Constructs spatial edges between SpatialNodes based on geometric relationships.
Pure geometry — no ML, no heuristics beyond distance/overlap thresholds.
"""
from typing import List
from src.pipeline.m5_semantic.graph.spatial_graph import SpatialNode, SpatialEdge, SpatialRelation

# Thresholds (in pixel units, tuned for typical 72-300 DPI documents)
VERTICAL_ADJACENCY_GAP = 30       # Max vertical gap for "adjacent" relation
HORIZONTAL_OVERLAP_MIN = 0.3      # Min x-overlap ratio for "same_column"
VERTICAL_OVERLAP_MIN = 0.3        # Min y-overlap ratio for "same_row"
CONTAINMENT_THRESHOLD = 0.85      # % area of child inside parent to count as "inside"


class EdgeBuilder:
    """
    Builds typed spatial edges between all node pairs on a page.
    Every node is guaranteed at least one edge (no orphans).
    """

    @staticmethod
    def build_edges(nodes: List[SpatialNode]) -> List[SpatialEdge]:
        """
        O(n²) pairwise edge construction. Acceptable for typical page sizes (< 200 nodes).
        """
        edges: List[SpatialEdge] = []
        connected = set()

        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if i == j:
                    continue

                new_edges = EdgeBuilder._compute_relations(a, b)
                for edge in new_edges:
                    edges.append(edge)
                    connected.add(a.node_id)
                    connected.add(b.node_id)

        # GUARANTEE: no orphan nodes — connect any isolated node to nearest neighbor
        orphans = [n for n in nodes if n.node_id not in connected]
        for orphan in orphans:
            nearest = EdgeBuilder._find_nearest(orphan, nodes)
            if nearest:
                edges.append(SpatialEdge(
                    from_node_id=orphan.node_id,
                    to_node_id=nearest.node_id,
                    relation=SpatialRelation.ADJACENT,
                    weight=EdgeBuilder._euclidean_distance(orphan, nearest)
                ))

        return edges

    @staticmethod
    def _compute_relations(a: SpatialNode, b: SpatialNode) -> List[SpatialEdge]:
        """Compute all applicable spatial relations from node a to node b."""
        result = []

        # --- Containment ---
        if EdgeBuilder._is_inside(a, b):
            result.append(SpatialEdge(
                from_node_id=a.node_id, to_node_id=b.node_id,
                relation=SpatialRelation.INSIDE,
                weight=0.1
            ))
            return result  # Containment is exclusive — skip other relations

        if EdgeBuilder._is_inside(b, a):
            result.append(SpatialEdge(
                from_node_id=a.node_id, to_node_id=b.node_id,
                relation=SpatialRelation.CONTAINS,
                weight=0.1
            ))
            return result

        # --- Vertical relationships (above/below) ---
        x_overlap = EdgeBuilder._x_overlap_ratio(a, b)
        if x_overlap > HORIZONTAL_OVERLAP_MIN:
            v_gap = b.y - a.y_max  # positive = b is below a

            if 0 <= v_gap <= VERTICAL_ADJACENCY_GAP:
                result.append(SpatialEdge(
                    from_node_id=a.node_id, to_node_id=b.node_id,
                    relation=SpatialRelation.BELOW,
                    weight=v_gap + 1.0
                ))
                result.append(SpatialEdge(
                    from_node_id=a.node_id, to_node_id=b.node_id,
                    relation=SpatialRelation.ADJACENT,
                    weight=v_gap + 1.0
                ))

        # --- Horizontal relationships (left/right) ---
        y_overlap = EdgeBuilder._y_overlap_ratio(a, b)
        if y_overlap > VERTICAL_OVERLAP_MIN:
            h_gap = b.x - a.x_max  # positive = b is right of a

            if 0 <= h_gap <= VERTICAL_ADJACENCY_GAP * 2:
                result.append(SpatialEdge(
                    from_node_id=a.node_id, to_node_id=b.node_id,
                    relation=SpatialRelation.RIGHT_OF,
                    weight=h_gap + 1.0
                ))

        # --- Same column detection ---
        if x_overlap > 0.5:
            dist = abs(a.cy - b.cy)
            result.append(SpatialEdge(
                from_node_id=a.node_id, to_node_id=b.node_id,
                relation=SpatialRelation.SAME_COLUMN,
                weight=dist
            ))

        # --- Same row detection ---
        if y_overlap > 0.5:
            dist = abs(a.cx - b.cx)
            result.append(SpatialEdge(
                from_node_id=a.node_id, to_node_id=b.node_id,
                relation=SpatialRelation.SAME_ROW,
                weight=dist
            ))

        return result

    # ── Geometric helpers ──

    @staticmethod
    def _x_overlap_ratio(a: SpatialNode, b: SpatialNode) -> float:
        """How much of a's x-range overlaps with b's x-range (0.0 to 1.0)."""
        overlap_start = max(a.x, b.x)
        overlap_end = min(a.x_max, b.x_max)
        overlap = max(0.0, overlap_end - overlap_start)
        min_width = min(a.width, b.width)
        return overlap / min_width if min_width > 0 else 0.0

    @staticmethod
    def _y_overlap_ratio(a: SpatialNode, b: SpatialNode) -> float:
        """How much of a's y-range overlaps with b's y-range (0.0 to 1.0)."""
        overlap_start = max(a.y, b.y)
        overlap_end = min(a.y_max, b.y_max)
        overlap = max(0.0, overlap_end - overlap_start)
        min_height = min(a.height, b.height)
        return overlap / min_height if min_height > 0 else 0.0

    @staticmethod
    def _is_inside(child: SpatialNode, parent: SpatialNode) -> bool:
        """Check if child bbox is mostly inside parent bbox."""
        if child.width * child.height == 0 or parent.width * parent.height == 0:
            return False

        inter_x = max(0, min(child.x_max, parent.x_max) - max(child.x, parent.x))
        inter_y = max(0, min(child.y_max, parent.y_max) - max(child.y, parent.y))
        inter_area = inter_x * inter_y
        child_area = child.width * child.height

        return (inter_area / child_area) >= CONTAINMENT_THRESHOLD if child_area > 0 else False

    @staticmethod
    def _euclidean_distance(a: SpatialNode, b: SpatialNode) -> float:
        return ((a.cx - b.cx) ** 2 + (a.cy - b.cy) ** 2) ** 0.5

    @staticmethod
    def _find_nearest(target: SpatialNode, nodes: List[SpatialNode]) -> SpatialNode | None:
        best = None
        best_dist = float('inf')
        for n in nodes:
            if n.node_id == target.node_id:
                continue
            d = EdgeBuilder._euclidean_distance(target, n)
            if d < best_dist:
                best_dist = d
                best = n
        return best
