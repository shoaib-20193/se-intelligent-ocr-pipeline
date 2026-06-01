"""
src/pipeline/m6_export/renderer.py
Transforms M6.5 LayoutSolvedDocument into a stateless RenderableDocument.
Applies dynamically solved layout parameters (font_size, alignment, wrap_mode)
directly to the final M6 semantic tokens.
"""
from typing import Dict, Any, List
from src.pipeline.m5_semantic.contracts import SemanticSpatialToken as M5Token
from src.pipeline.m6_5_layout.contracts import LayoutSolvedDocument, RenderInstruction
from src.pipeline.m6_export.contracts import RenderableDocument, RenderablePage, SemanticSpatialToken


class DocumentRenderer:
    """
    Stateless block-level transformer.
    Converts M6.5 LayoutSolvedDocument into M6 renderable tokens.
    Geometry passes through UNMODIFIED. 
    Styling is applied exactly as dictated by the M6.5 ConstraintSolver.
    """

    @staticmethod
    def render(doc: LayoutSolvedDocument) -> RenderableDocument:
        renderable_pages = []

        for solved_page in doc.pages:
            page = solved_page.structured_page
            instructions = solved_page.render_instructions
            
            tokens = []

            page_width = float(page.page_width)
            page_height = float(page.page_height)

            for m5_token in page.tokens:
                instruction = instructions.get(m5_token.token_id)
                if instruction:
                    tokens.append(DocumentRenderer._render_block(m5_token, instruction, page_width, page_height))

            num_columns = 1
            if hasattr(page, 'spatial_graph') and page.spatial_graph is not None:
                num_columns = page.spatial_graph.num_columns

            renderable_pages.append(RenderablePage(
                page_number=page.page_number,
                width=page_width,
                height=page_height,
                num_columns=num_columns,
                tokens=tokens
            ))

        return RenderableDocument(
            document_id=doc.source_document_id,
            pages=renderable_pages,
            metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else {}
        )

    @staticmethod
    def _render_block(m5_token: M5Token, instruction: RenderInstruction, page_width: float, page_height: float) -> SemanticSpatialToken:
        b_type = m5_token.block_type.lower()

        # Geometry — DIRECT from M5, NO modification
        x = m5_token.bbox.x_min
        y = m5_token.bbox.y_min
        width = m5_token.bbox.x_max - m5_token.bbox.x_min
        height = m5_token.bbox.y_max - m5_token.bbox.y_min

        # Store solved alignment and wrap_mode inside spatial_metadata for downstream exporters
        metadata = m5_token.spatial_metadata.copy() if hasattr(m5_token, 'spatial_metadata') else {}
        metadata["wrap_mode"] = instruction.wrap_mode
        metadata["line_spacing"] = instruction.line_spacing

        return SemanticSpatialToken(
            token_id=m5_token.token_id,
            text=m5_token.text,
            block_type=b_type,
            x=x,
            y=y,
            width=width,
            height=height,
            page_width=page_width,
            page_height=page_height,
            font_size=instruction.font_size,
            font_weight=instruction.font_weight,
            alignment=instruction.alignment,
            source_region_ids=[m5_token.source_region_id],
            reading_order=m5_token.reading_order,
            confidence=m5_token.confidence,
            column_id=m5_token.column_id,
            spatial_metadata=metadata
        )
