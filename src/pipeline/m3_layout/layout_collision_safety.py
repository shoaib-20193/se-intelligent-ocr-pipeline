"""
src/pipeline/m3_layout/layout_collision_safety.py
M3 Layout Collision Safety Engine (Force Field Model).

Detects spatial collisions using virtual bounding boxes and generates
repulsion constraints (force vectors) WITHOUT modifying ground-truth geometry.
M3 detects stress; downstream layers (M5/M6) resolve it.
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Any
from src.data_model.layout import Region


class LayoutCollisionSafetyEngine:
    VIRTUAL_PADDING_X = 4.0
    VIRTUAL_PADDING_Y = 6.0

    @classmethod
    def process(cls, regions: List[Region], page_width: int, page_height: int) -> List[Region]:
        """
        Process regions to attach collision safety constraints.
        Does not mutate the `bbox` of any region.
        Returns new Region objects with enriched `spatial_metadata`.
        """
        if not regions:
            return []

        virtual_bboxes = []
        for r in regions:
            x1, y1, x2, y2 = r.bbox
            vx1 = max(0.0, x1 - cls.VIRTUAL_PADDING_X)
            vy1 = max(0.0, y1 - cls.VIRTUAL_PADDING_Y)
            vx2 = min(float(page_width), x2 + cls.VIRTUAL_PADDING_X)
            vy2 = min(float(page_height), y2 + cls.VIRTUAL_PADDING_Y)
            virtual_bboxes.append((vx1, vy1, vx2, vy2))

        # Build collision matrix and repulsion vectors
        enriched_regions = []
        n = len(regions)
        
        for i in range(n):
            r = regions[i]
            vx1, vy1, vx2, vy2 = virtual_bboxes[i]
            x1, y1, x2, y2 = r.bbox
            area = max(1.0, float((x2 - x1) * (y2 - y1)))

            total_overlap_area = 0.0
            force_x = 0.0
            force_y = 0.0
            colliding_neighbors = []

            for j in range(n):
                if i == j:
                    continue
                    
                ovx1, ovy1, ovx2, ovy2 = virtual_bboxes[j]
                
                # Check intersection of virtual bboxes
                ix1 = max(vx1, ovx1)
                iy1 = max(vy1, ovy1)
                ix2 = min(vx2, ovx2)
                iy2 = min(vy2, ovy2)
                
                if ix1 < ix2 and iy1 < iy2:
                    # Virtual Collision Detected
                    colliding_neighbors.append(regions[j].id)
                    overlap_w = ix2 - ix1
                    overlap_h = iy2 - iy1
                    overlap_area = overlap_w * overlap_h
                    total_overlap_area += overlap_area
                    
                    # Compute directional repulsion force away from neighbor
                    # Force is proportional to overlap depth. 
                    # If neighbor is to the right, we push left (negative force_x)
                    r_cx = (x1 + x2) / 2.0
                    r_cy = (y1 + y2) / 2.0
                    
                    o_x1, o_y1, o_x2, o_y2 = regions[j].bbox
                    o_cx = (o_x1 + o_x2) / 2.0
                    o_cy = (o_y1 + o_y2) / 2.0
                    
                    dx = r_cx - o_cx
                    dy = r_cy - o_cy
                    
                    # Distribute force based on relative positioning
                    if abs(dx) > abs(dy):
                        # Primarily horizontal conflict
                        sign_x = 1.0 if dx > 0 else -1.0
                        force_x += sign_x * overlap_w
                    else:
                        # Primarily vertical conflict
                        sign_y = 1.0 if dy > 0 else -1.0
                        force_y += sign_y * overlap_h

            collision_pressure = total_overlap_area / area

            # Update metadata
            new_meta = r.spatial_metadata.copy() if hasattr(r, 'spatial_metadata') and r.spatial_metadata else {}
            new_meta["virtual_bbox"] = (vx1, vy1, vx2, vy2)
            new_meta["collision_pressure"] = collision_pressure
            new_meta["repulsion_vector"] = (force_x, force_y)
            new_meta["colliding_neighbors"] = colliding_neighbors

            # Create new region with unmodified ground-truth bbox
            enriched_regions.append(Region(
                id=r.id,
                bbox=r.bbox,
                polygon=r.polygon,
                confidence=r.confidence,
                type=r.type,
                spatial_metadata=new_meta,
                crop_ref=r.crop_ref
            ))

        return enriched_regions
