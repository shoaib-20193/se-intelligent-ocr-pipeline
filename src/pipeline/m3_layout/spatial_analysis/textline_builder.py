"""
Textline Builder — merge DocTR word-level boxes into stable line-level regions.
Prevents graph explosion, stabilizes paragraph clustering, reduces noisy reading order.
Strictly spatial/geometric only. No semantic inference.
"""
from __future__ import annotations
from typing import List
from src.data_model.layout import Region
from src.utils.bbox_utils import iou


def _merge_bboxes(bboxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    """Merge a list of bboxes into a single surrounding bbox."""
    x1 = min(b[0] for b in bboxes)
    y1 = min(b[1] for b in bboxes)
    x2 = max(b[2] for b in bboxes)
    y2 = max(b[3] for b in bboxes)
    return (x1, y1, x2, y2)


def _avg_confidence(regions: list[Region]) -> float:
    if not regions:
        return 0.0
    return sum(r.confidence for r in regions) / len(regions)


def _same_line(r1: Region, r2: Region, line_height_tol: float = 0.5, x_gap_max: float = 0.02,
               page_width: int = 1) -> bool:
    """
    Determine if two word-level regions are on the same line.
    Criteria: vertical center overlap, small horizontal gap.
    """
    # vertical band overlap using midpoints
    mid1 = (r1.y1 + r1.y2) / 2.0
    mid2 = (r2.y1 + r2.y2) / 2.0
    avg_h = max(1, (r1.height + r2.height) / 2.0)
    v_diff = abs(mid1 - mid2)
    if v_diff > avg_h * line_height_tol:
        return False
    # horizontal gap check — right edge of r1 to left edge of r2 (or vice versa)
    gap = max(r1.x1, r2.x1) - min(r1.x2, r2.x2)
    max_gap = x_gap_max * page_width
    return gap <= max_gap


def build_textlines(
    word_regions: List[Region],
    page_number: int,
    page_width: int,
    line_height_tol: float = 0.5,
    x_gap_max_fraction: float = 0.03,
) -> List[Region]:
    """
    Merge word-level regions into line-level regions using horizontal proximity
    and vertical alignment.

    Returns new Region objects with type='text_block', spatial_metadata preserved.
    Original regions are not mutated.
    """
    if not word_regions:
        return []

    # Sort by y1 then x1 for stable grouping
    sorted_words = sorted(word_regions, key=lambda r: (r.y1, r.x1))

    lines: list[list[Region]] = []
    current_line: list[Region] = [sorted_words[0]]

    for word in sorted_words[1:]:
        prev = current_line[-1]
        if _same_line(prev, word, line_height_tol=line_height_tol, x_gap_max=x_gap_max_fraction,
                      page_width=page_width):
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
    lines.append(current_line)

    line_regions: list[Region] = []
    for line_idx, line_words in enumerate(lines):
        merged_bbox = _merge_bboxes([w.bbox for w in line_words])
        avg_conf = _avg_confidence(line_words)
        # Sort words left-to-right within each line
        line_words_sorted = sorted(line_words, key=lambda r: r.x1)
        first_word = line_words_sorted[0]
        # Preserve crop_ref of leftmost word as line anchor
        line_regions.append(Region(
            id=f"p{page_number}-l{line_idx}",
            bbox=merged_bbox,
            polygon=None,
            confidence=avg_conf,
            type="text_block",
            spatial_metadata={
                "word_count": len(line_words),
                "word_ids": [w.id for w in line_words],
            },
            crop_ref=first_word.crop_ref,
        ))

    return line_regions
