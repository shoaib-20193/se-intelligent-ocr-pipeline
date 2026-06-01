"""
src/pipeline/m6_5_layout/contracts.py
Output contracts for the M6.5 Layout Constraint Solver Engine.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.pipeline.m5_semantic.contracts import StructuredPage, StructuredDocument

@dataclass
class RenderInstruction:
    """
    Resolved layout parameters for a specific document block.
    Output of the constraint solver.
    """
    block_id: str
    
    font_size: float
    font_weight: int
    line_spacing: float
    alignment: str  # "left", "center", "right", "justify"
    wrap_mode: str  # "soft_wrap", "hard_wrap", "none"
    
    fit_status: str  # "fits", "shrunk", "wrapped", "overflow_resolved", "warning"
    overflow_strategy_used: List[str] = field(default_factory=list)


@dataclass
class LayoutSolvedPage:
    """
    A page containing blocks and their corresponding RenderInstructions.
    """
    page_number: int
    # Original M5 page
    structured_page: StructuredPage
    # Map of block_id -> RenderInstruction
    render_instructions: Dict[str, RenderInstruction]


@dataclass
class LayoutSolvedDocument:
    """
    The canonical input for M6 Rendering.
    Contains the structured blocks + their exact rendering instructions.
    """
    source_document_id: str
    pages: List[LayoutSolvedPage]
    metadata: Dict[str, Any]
