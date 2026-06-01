"""
src/pipeline/m5_semantic/graph/spatial_graph.py
Core data structures for the Spatial Graph Engine.
Nodes = M3 regions with text. Edges = spatial relationships.
This is the document's topology — a DOM for scanned pages.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class SpatialRelation(str, Enum):
    """Typed spatial relationship between two nodes."""
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    INSIDE = "inside"
    CONTAINS = "contains"
    SAME_COLUMN = "same_column"
    SAME_ROW = "same_row"
    ADJACENT = "adjacent"


@dataclass
class SpatialNode:
    """
    A node in the spatial graph. Each node corresponds to one M3 region
    with attached M4 OCR text. The bbox is IMMUTABLE — it comes from M3.
    """
    node_id: str
    text: str
    
    # Geometry — M3 AUTHORITATIVE, NEVER MODIFIED
    x: float
    y: float
    width: float
    height: float
    
    page_number: int
    source_region_id: str
    confidence: float
    
    # Assigned by graph engine (not by caller)
    semantic_label: str = "unknown"  # heading | paragraph | list | table | unknown
    column_id: int = -1             # Assigned by ColumnDetector
    resolved_reading_order: int = 0  # Assigned by ReadingOrderSolver
    cluster_id: int = -1            # Assigned by grouping phase
    
    @property
    def cx(self) -> float:
        """Center x coordinate."""
        return self.x + self.width / 2.0
    
    @property
    def cy(self) -> float:
        """Center y coordinate."""
        return self.y + self.height / 2.0
    
    @property
    def y_max(self) -> float:
        """Bottom edge."""
        return self.y + self.height
    
    @property
    def x_max(self) -> float:
        """Right edge."""
        return self.x + self.width


@dataclass
class SpatialEdge:
    """
    A directed edge representing a spatial relationship between two nodes.
    Weight encodes spatial proximity (lower = closer).
    """
    from_node_id: str
    to_node_id: str
    relation: SpatialRelation
    weight: float = 1.0


@dataclass
class SpatialGraph:
    """
    The complete spatial topology of a single page.
    This is the structured document DOM for scanned pages.
    """
    page_number: int
    nodes: List[SpatialNode] = field(default_factory=list)
    edges: List[SpatialEdge] = field(default_factory=list)
    
    # Index maps built after construction
    _node_map: dict = field(default_factory=dict, repr=False)
    _adjacency: dict = field(default_factory=dict, repr=False)
    
    def build_index(self):
        """Build O(1) lookup indices after nodes/edges are populated."""
        self._node_map = {n.node_id: n for n in self.nodes}
        self._adjacency = {n.node_id: [] for n in self.nodes}
        for edge in self.edges:
            self._adjacency[edge.from_node_id].append(edge)
    
    def get_node(self, node_id: str) -> Optional[SpatialNode]:
        return self._node_map.get(node_id)
    
    def get_edges_from(self, node_id: str) -> List[SpatialEdge]:
        return self._adjacency.get(node_id, [])
    
    def get_neighbors(self, node_id: str, relation: Optional[SpatialRelation] = None) -> List[SpatialNode]:
        """Get all neighbor nodes, optionally filtered by relation type."""
        edges = self.get_edges_from(node_id)
        if relation:
            edges = [e for e in edges if e.relation == relation]
        return [self._node_map[e.to_node_id] for e in edges if e.to_node_id in self._node_map]
    
    def get_nodes_in_column(self, column_id: int) -> List[SpatialNode]:
        """Get all nodes belonging to a specific column, sorted by y position."""
        return sorted(
            [n for n in self.nodes if n.column_id == column_id],
            key=lambda n: (n.y, n.x)
        )
    
    def get_resolved_order(self) -> List[SpatialNode]:
        """Get all nodes in their final resolved reading order."""
        return sorted(self.nodes, key=lambda n: n.resolved_reading_order)
    
    @property
    def num_columns(self) -> int:
        col_ids = set(n.column_id for n in self.nodes if n.column_id >= 0)
        return len(col_ids) if col_ids else 1
