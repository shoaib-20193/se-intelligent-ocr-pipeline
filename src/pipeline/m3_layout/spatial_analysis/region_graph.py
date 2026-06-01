"""
Region Graph — spatial adjacency graph generation using grid-bucketed neighbor search.
Avoids O(n²) naive search. Strictly spatial/geometric. No semantic inference.
Populates spatial_metadata["adjacency_links"] and spatial_metadata["cluster_id"].
"""
from __future__ import annotations
from typing import List
from collections import defaultdict
from src.data_model.layout import Region


def _grid_key(x: int, y: int, cell_size: int) -> tuple[int, int]:
    return (x // cell_size, y // cell_size)


def _candidate_neighbors(
    region: Region, index: dict[tuple[int, int], list[int]], all_regions: List[Region],
    cell_size: int, max_distance_px: int
) -> list[int]:
    """Return indices of candidate neighbors using grid bucket lookup."""
    cx = int(region.center_x)
    cy = int(region.center_y)
    radius_cells = (max_distance_px // cell_size) + 1
    gx, gy = _grid_key(cx, cy, cell_size)
    candidates = []
    for dx in range(-radius_cells, radius_cells + 1):
        for dy in range(-radius_cells, radius_cells + 1):
            for idx in index.get((gx + dx, gy + dy), []):
                candidates.append(idx)
    return candidates


def _bbox_gap(r1: Region, r2: Region) -> int:
    """
    Minimum axis-aligned gap between two bboxes.
    Negative means they overlap.
    """
    h_gap = max(r1.x1, r2.x1) - min(r1.x2, r2.x2)
    v_gap = max(r1.y1, r2.y1) - min(r1.y2, r2.y2)
    return max(h_gap, v_gap)


def build_region_graph(
    regions: List[Region],
    page_width: int,
    page_height: int,
    max_neighbor_distance_fraction: float = 0.08,
) -> List[Region]:
    """
    Build a spatial adjacency graph over line-level regions.
    Each region gets:
      spatial_metadata["adjacency_links"]: list of adjacent region IDs
      spatial_metadata["cluster_id"]: connected component ID

    Uses grid-bucketed spatial index to avoid O(n²).
    """
    if not regions:
        return regions

    max_dist_px = max(10, int(max(page_width, page_height) * max_neighbor_distance_fraction))
    cell_size = max(20, max_dist_px // 3)

    # Build spatial grid index
    grid_index: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, r in enumerate(regions):
        key = _grid_key(int(r.center_x), int(r.center_y), cell_size)
        grid_index[key].append(idx)

    # Compute adjacency lists
    adjacency: dict[str, list[str]] = {r.id: [] for r in regions}
    region_by_idx = {i: r for i, r in enumerate(regions)}

    for i, r in enumerate(regions):
        candidates = _candidate_neighbors(r, grid_index, regions, cell_size, max_dist_px)
        for j in candidates:
            if j == i:
                continue
            neighbor = region_by_idx[j]
            gap = _bbox_gap(r, neighbor)
            if gap <= max_dist_px:
                if neighbor.id not in adjacency[r.id]:
                    adjacency[r.id].append(neighbor.id)

    # Connected components via BFS → cluster_id
    cluster_id_map: dict[str, int] = {}
    cluster_counter = 0
    for r in regions:
        if r.id in cluster_id_map:
            continue
        # BFS
        queue = [r.id]
        cluster_id_map[r.id] = cluster_counter
        head = 0
        while head < len(queue):
            current_id = queue[head]
            head += 1
            for neighbor_id in adjacency.get(current_id, []):
                if neighbor_id not in cluster_id_map:
                    cluster_id_map[neighbor_id] = cluster_counter
                    queue.append(neighbor_id)
        cluster_counter += 1

    # Build updated regions
    updated = []
    for r in regions:
        new_meta = dict(r.spatial_metadata)
        new_meta["adjacency_links"] = adjacency.get(r.id, [])
        new_meta["cluster_id"] = cluster_id_map.get(r.id, -1)
        updated.append(Region(
            id=r.id,
            bbox=r.bbox,
            polygon=r.polygon,
            confidence=r.confidence,
            type="text_block",
            spatial_metadata=new_meta,
            crop_ref=r.crop_ref,
        ))
    return updated
