"""
src/pipeline/m6_5_layout/solver.py
M6.5 Layout Constraint Solver Engine.
Computes optimal rendering parameters (font_size, line_spacing, wrap_mode)
to ensure text perfectly fits inside M3's immutable bounding boxes.
"""
import logging
from typing import Dict, List, Tuple
from src.pipeline.m5_semantic.contracts import StructuredDocument, SemanticSpatialToken
from src.pipeline.m6_5_layout.contracts import (
    RenderInstruction, LayoutSolvedPage, LayoutSolvedDocument
)

logger = logging.getLogger(__name__)

# Constants for layout solving
FONT_MIN_SIZE = 6.0
FONT_MAX_SIZE = 18.0
DEFAULT_LINE_SPACING = 1.2
CHAR_WIDTH_RATIO = 0.55  # Rough average width-to-height ratio for standard fonts


class ConstraintSolver:
    """
    Determines rendering parameters deterministically without touching geometry.
    """

    @staticmethod
    def solve(document: StructuredDocument) -> LayoutSolvedDocument:
        solved_pages = []

        for page in document.pages:
            instructions = {}

            for token in page.tokens:
                b_type = token.block_type.lower()
                
                if b_type == "table":
                    instruction = ConstraintSolver._solve_table(token)
                elif b_type == "heading":
                    instruction = ConstraintSolver._solve_heading(token)
                elif b_type == "key_value_pair":
                    instruction = ConstraintSolver._solve_kv(token)
                else:
                    # Paragraphs, lists, unknown
                    instruction = ConstraintSolver._solve_text_block(token)
                
                instructions[token.token_id] = instruction
            
            solved_pages.append(LayoutSolvedPage(
                page_number=page.page_number,
                structured_page=page,
                render_instructions=instructions
            ))
            
            logger.info(f"[M6.5] Page {page.page_number}: Solved layout for {len(instructions)} blocks")

        return LayoutSolvedDocument(
            source_document_id=document.source_document_id,
            pages=solved_pages,
            metadata=document.metadata
        )

    @staticmethod
    def _solve_text_block(token: SemanticSpatialToken) -> RenderInstruction:
        """Solves constraint for standard text blocks by wrapping first, shrinking second."""
        bbox_w = max(token.bbox.x_max - token.bbox.x_min, 1)
        bbox_h = max(token.bbox.y_max - token.bbox.y_min, 1)
        
        font_size = 12.0
        line_spacing = DEFAULT_LINE_SPACING
        strategies_used = []
        status = "fits"
        
        # Calculate raw text width at 12pt
        max_line_len = max((len(line) for line in token.text.split("\n")), default=1)
        raw_width = max_line_len * font_size * CHAR_WIDTH_RATIO
        
        # 1. Check if it needs wrapping
        if raw_width > bbox_w:
            strategies_used.append("wrap_text")
            status = "wrapped"
            # Estimate new height after wrapping
            chars_per_line = max(int(bbox_w / (font_size * CHAR_WIDTH_RATIO)), 1)
            num_lines = sum(max(1, len(line) / chars_per_line) for line in token.text.split("\n"))
        else:
            num_lines = len(token.text.split("\n"))
            
        est_height = num_lines * font_size * line_spacing
        
        # 2. Check if it fits vertically. If not, shrink font.
        if est_height > bbox_h:
            status = "shrunk"
            strategies_used.append("shrink_font")
            
            # Find font size that fits height
            # bbox_h = num_lines * f_size * line_spacing
            # But wait, num_lines changes if f_size changes (wrapping).
            # We'll use a simple iterative approach.
            while font_size > FONT_MIN_SIZE:
                font_size -= 0.5
                chars_per_line = max(int(bbox_w / (font_size * CHAR_WIDTH_RATIO)), 1)
                num_lines = sum(max(1, len(line) / chars_per_line) for line in token.text.split("\n"))
                est_height = num_lines * font_size * line_spacing
                if est_height <= bbox_h:
                    break
                    
            if font_size <= FONT_MIN_SIZE and est_height > bbox_h:
                # Still doesn't fit, reduce line spacing as last resort
                strategies_used.append("adjust_spacing")
                line_spacing = max(1.0, bbox_h / (num_lines * font_size))
                status = "warning"
                
        alignment = "left"
        if token.spatial_metadata.get("layout_role") == "full_width":
            alignment = "justify"

        return RenderInstruction(
            block_id=token.token_id,
            font_size=max(font_size, FONT_MIN_SIZE),
            font_weight=400,
            line_spacing=line_spacing,
            alignment=alignment,
            wrap_mode="soft_wrap",
            fit_status=status,
            overflow_strategy_used=strategies_used
        )

    @staticmethod
    def _solve_heading(token: SemanticSpatialToken) -> RenderInstruction:
        """Headings prefer wrapping over shrinking, default large font."""
        bbox_w = max(token.bbox.x_max - token.bbox.x_min, 1)
        font_size = 18.0
        strategies = []
        status = "fits"
        
        raw_width = len(token.text) * font_size * CHAR_WIDTH_RATIO
        if raw_width > bbox_w:
            strategies.append("wrap_text")
            status = "wrapped"
            
            # If it's extremely wrapped (e.g. > 3 lines), shrink it a bit
            chars_per_line = max(int(bbox_w / (font_size * CHAR_WIDTH_RATIO)), 1)
            num_lines = len(token.text) / chars_per_line
            if num_lines > 2:
                font_size = 14.0
                strategies.append("shrink_font")
                status = "shrunk"

        alignment = "center" if token.spatial_metadata.get("layout_role") == "full_width" else "left"

        return RenderInstruction(
            block_id=token.token_id,
            font_size=font_size,
            font_weight=700,
            line_spacing=DEFAULT_LINE_SPACING,
            alignment=alignment,
            wrap_mode="soft_wrap",
            fit_status=status,
            overflow_strategy_used=strategies
        )

    @staticmethod
    def _solve_table(token: SemanticSpatialToken) -> RenderInstruction:
        """
        Tables MUST use a global font size for consistency across all rows.
        Shrink font until the longest cell text fits within its column.
        """
        bbox_w = max(token.bbox.x_max - token.bbox.x_min, 1)
        font_size = 11.0
        strategies = []
        status = "fits"
        
        table_rows = token.spatial_metadata.get("table_rows", [])
        if not table_rows:
            return RenderInstruction(
                block_id=token.token_id, font_size=11.0, font_weight=400,
                line_spacing=1.0, alignment="left", wrap_mode="none",
                fit_status="warning", overflow_strategy_used=[]
            )

        num_cols = max(len(row) for row in table_rows)
        if num_cols == 0: num_cols = 1
        
        # Estimate col width evenly (in reality could be variable, but bbox assumes even grid in current M6 renderer)
        col_width = bbox_w / num_cols
        
        # Find longest cell
        max_cell_len = max((len(cell) for row in table_rows for cell in row), default=1)
        
        while font_size > FONT_MIN_SIZE:
            raw_width = max_cell_len * font_size * CHAR_WIDTH_RATIO
            if raw_width <= col_width:
                break
            font_size -= 0.5
            strategies.append("shrink_font")
            status = "shrunk"

        # If still doesn't fit, it will wrap inside the cell.
        if font_size <= FONT_MIN_SIZE and raw_width > col_width:
            strategies.append("wrap_text")
            status = "warning"

        return RenderInstruction(
            block_id=token.token_id,
            font_size=max(font_size, FONT_MIN_SIZE),
            font_weight=400,
            line_spacing=1.0,  # Tables usually tighter
            alignment="left",
            wrap_mode="soft_wrap",
            fit_status=status,
            overflow_strategy_used=strategies
        )

    @staticmethod
    def _solve_kv(token: SemanticSpatialToken) -> RenderInstruction:
        """KV pairs check if label + value exceeds width. If so, hard wrap value."""
        bbox_w = max(token.bbox.x_max - token.bbox.x_min, 1)
        font_size = 11.0
        strategies = []
        status = "fits"
        wrap_mode = "none"
        
        max_line_len = max((len(line) for line in token.text.split("\n")), default=1)
        raw_width = max_line_len * font_size * CHAR_WIDTH_RATIO
        
        if raw_width > bbox_w:
            strategies.append("enable_multiline")
            status = "wrapped"
            wrap_mode = "hard_wrap"  # Push value to next line
            
        return RenderInstruction(
            block_id=token.token_id,
            font_size=font_size,
            font_weight=400,
            line_spacing=DEFAULT_LINE_SPACING,
            alignment="left",
            wrap_mode=wrap_mode,
            fit_status=status,
            overflow_strategy_used=strategies
        )
