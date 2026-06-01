"""
Layout Visualization — debug overlays for M3 spatial analysis outputs.
Saves images to data/debug/layout/ for visual inspection.
"""
from __future__ import annotations
import os
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("[layout_viz] OpenCV not available — visualization disabled.")

from src.data_model.layout import LayoutPage, Region

DEBUG_DIR = "data/debug/layout"

_CLUSTER_COLORS = [
    (220, 80, 80), (80, 180, 80), (80, 80, 220), (200, 160, 40),
    (160, 80, 200), (40, 200, 200), (200, 120, 40), (120, 200, 40),
    (200, 40, 160), (40, 120, 200),
]


def _get_color(cluster_id: int) -> tuple[int, int, int]:
    return _CLUSTER_COLORS[cluster_id % len(_CLUSTER_COLORS)]


def draw_layout_overlay(
    image: np.ndarray,
    page: LayoutPage,
    show_reading_order: bool = True,
    show_clusters: bool = True,
    show_adjacency: bool = False,
    show_column_bands: bool = True,
) -> np.ndarray:
    """
    Draw all M3 spatial analysis overlays onto a copy of `image`.
    Returns the annotated image. Original image is NOT mutated.
    """
    if not _CV2_AVAILABLE:
        return image

    canvas = image.copy()
    h, w = canvas.shape[:2]

    # Draw column bands as vertical lines
    if show_column_bands and page.column_count > 1:
        col_w = w // page.column_count
        for col in range(1, page.column_count):
            x = col * col_w
            cv2.line(canvas, (x, 0), (x, h), (180, 180, 180), 1, cv2.LINE_AA)

    id_to_region = {r.id: r for r in page.regions}

    for region in page.regions:
        x1, y1, x2, y2 = region.bbox
        cluster_id = region.spatial_metadata.get("cluster_id", 0)
        reading_order = region.spatial_metadata.get("reading_order", -1)
        table_cand = region.spatial_metadata.get("table_candidate", False)
        para_cand = region.spatial_metadata.get("paragraph_candidate", False)

        # Choose box color
        if show_clusters:
            color = _get_color(cluster_id)
        else:
            color = (100, 200, 100)

        thickness = 2 if (table_cand or para_cand) else 1
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)

        # Reading order number
        if show_reading_order and reading_order >= 0:
            label = str(reading_order)
            font_scale = 0.45
            cv2.putText(canvas, label, (x1 + 2, y1 + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(canvas, label, (x1 + 2, y1 + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (40, 40, 40), 1, cv2.LINE_AA)

        # Table candidate marker
        if table_cand:
            cv2.rectangle(canvas, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (0, 200, 255), 2)

        # Adjacency graph edges
        if show_adjacency:
            cx1 = (x1 + x2) // 2
            cy1 = (y1 + y2) // 2
            for neighbor_id in region.spatial_metadata.get("adjacency_links", []):
                neighbor = id_to_region.get(neighbor_id)
                if neighbor:
                    cx2 = (neighbor.x1 + neighbor.x2) // 2
                    cy2 = (neighbor.y1 + neighbor.y2) // 2
                    cv2.line(canvas, (cx1, cy1), (cx2, cy2), (200, 160, 40), 1, cv2.LINE_AA)

    return canvas


def save_layout_debug(
    image: np.ndarray,
    page: LayoutPage,
    document_id: str,
    show_adjacency: bool = False,
) -> Optional[str]:
    """
    Draw overlays and save to data/debug/layout/{document_id}_p{page_number}.png.
    Returns saved path or None on failure.
    """
    if not _CV2_AVAILABLE:
        return None
    try:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        annotated = draw_layout_overlay(image, page, show_adjacency=show_adjacency)
        filename = f"{document_id}_p{page.page_number:04d}.png"
        path = os.path.join(DEBUG_DIR, filename)
        cv2.imwrite(path, annotated)
        logger.debug(f"[layout_viz] Saved debug overlay: {path}")
        return path
    except Exception as e:
        logger.warning(f"[layout_viz] Failed to save debug image: {e}")
        return None
