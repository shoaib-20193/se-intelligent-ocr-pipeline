"""
src/pipeline/m5_semantic/graph/column_detector.py
Detects multi-column layouts by clustering node x-coordinates.
Uses histogram peak detection (no ML, no external dependencies).
"""
from typing import List, Dict
from src.pipeline.m5_semantic.graph.spatial_graph import SpatialNode

# Minimum gap between column centers to count as separate columns
MIN_COLUMN_GAP_RATIO = 0.15  # 15% of page width


class ColumnDetector:
    """
    Assigns column_id to each SpatialNode based on x-coordinate distribution.
    Uses histogram binning + peak detection instead of k-means.
    """

    @staticmethod
    def detect_and_assign(nodes: List[SpatialNode], page_width: float = 800.0) -> int:
        """
        Detects columns and assigns column_id to each node in-place.
        Returns the number of detected columns.
        """
        if not nodes:
            return 0

        if len(nodes) == 1:
            nodes[0].column_id = 0
            return 1

        # Step 1: Collect center-x values
        cx_values = [(n, n.cx) for n in nodes]

        # Step 2: Find column centers via histogram peak detection
        num_bins = max(10, int(page_width / 40))  # ~40px per bin
        column_centers = ColumnDetector._find_peaks(
            [cx for _, cx in cx_values], num_bins, page_width
        )

        if not column_centers:
            # Fallback: single column
            for n in nodes:
                n.column_id = 0
            return 1

        # Step 3: Merge columns that are too close
        min_gap = page_width * MIN_COLUMN_GAP_RATIO
        merged_centers = ColumnDetector._merge_close_centers(column_centers, min_gap)

        # Step 4: Assign each node to the nearest column center
        # Sort centers left-to-right so column_id 0 = leftmost
        merged_centers.sort()

        for node in nodes:
            best_col = 0
            best_dist = float('inf')
            for col_idx, center in enumerate(merged_centers):
                dist = abs(node.cx - center)
                if dist < best_dist:
                    best_dist = dist
                    best_col = col_idx
            node.column_id = best_col

        return len(merged_centers)

    @staticmethod
    def _find_peaks(values: List[float], num_bins: int, page_width: float) -> List[float]:
        """
        Simple histogram peak detection.
        Returns x-coordinate centers of detected peaks.
        """
        if not values:
            return []

        bin_width = page_width / num_bins
        histogram = [0] * num_bins

        for v in values:
            bin_idx = min(int(v / bin_width), num_bins - 1)
            bin_idx = max(0, bin_idx)
            histogram[bin_idx] += 1

        # Find peaks: bins with count > neighbors (local maxima)
        # Minimum peak height: at least 2 nodes or 10% of total
        min_peak_height = max(2, len(values) * 0.08)
        peaks = []

        for i in range(num_bins):
            if histogram[i] < min_peak_height:
                continue

            left = histogram[i - 1] if i > 0 else 0
            right = histogram[i + 1] if i < num_bins - 1 else 0

            if histogram[i] >= left and histogram[i] >= right:
                # Peak center = middle of the bin
                peak_center = (i + 0.5) * bin_width
                peaks.append(peak_center)

        # Fallback: if no peaks found, use the median as single column
        if not peaks:
            sorted_vals = sorted(values)
            peaks = [sorted_vals[len(sorted_vals) // 2]]

        return peaks

    @staticmethod
    def _merge_close_centers(centers: List[float], min_gap: float) -> List[float]:
        """Merge column centers that are closer than min_gap."""
        if not centers:
            return []

        sorted_centers = sorted(centers)
        merged = [sorted_centers[0]]

        for c in sorted_centers[1:]:
            if c - merged[-1] < min_gap:
                # Merge: average the two
                merged[-1] = (merged[-1] + c) / 2.0
            else:
                merged.append(c)

        return merged
