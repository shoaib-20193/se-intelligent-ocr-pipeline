"""
src/pipeline/m6_export/interface.py
The core engine for the M6 Export Layer.
Provides a deterministic, stateless bridge between M5 StructuredDocument and the PyQt6 GUI.
"""
from typing import Dict, Any

from src.pipeline.m5_semantic.contracts import StructuredDocument
from src.pipeline.m6_export.contracts import RenderableDocument
from src.pipeline.m6_export.renderer import DocumentRenderer

from src.pipeline.m6_export.exporters.json_exporter import JsonExporter
from src.pipeline.m6_export.exporters.txt_exporter import TxtExporter
from src.pipeline.m6_export.exporters.md_exporter import MdExporter
from src.pipeline.m6_export.exporters.pdf_exporter import PdfExporter
from src.pipeline.m6_export.exporters.docx_exporter import DocxExporter


class M6ExportEngine:
    """
    Acts as the document compiler. It is stateless and does not infer semantic meaning.
    It simply converts a StructuredDocument into a strictly formatted RenderableDocument,
    and handles file serialization to all supported formats.
    """

    @staticmethod
    def to_renderable(structured_doc: StructuredDocument) -> RenderableDocument:
        """
        Transforms M5 output into M6 Renderable contract in O(n) time.
        First, passes the document through the M6.5 ConstraintSolver to determine optimal typography.
        Then, passes the solved document to the DocumentRenderer.
        """
        from src.pipeline.m6_5_layout.solver import ConstraintSolver
        
        # M6.5: Determine layout parameters to fit fixed M3 bboxes
        layout_solved_doc = ConstraintSolver.solve(structured_doc)
        
        # M6: Compile into RenderableDocument
        return DocumentRenderer.render(layout_solved_doc)

    @staticmethod
    def export_json(renderable_doc: RenderableDocument, output_path: str) -> str:
        """Exports to JSON (spatial-first format). Returns absolute path."""
        return JsonExporter.export(renderable_doc, output_path)

    @staticmethod
    def export_txt(renderable_doc: RenderableDocument, output_path: str) -> str:
        """Exports to TXT with spatial debug annotations. Returns absolute path."""
        return TxtExporter.export(renderable_doc, output_path)

    @staticmethod
    def export_md(renderable_doc: RenderableDocument, output_path: str) -> str:
        """Exports to Markdown with spatial HTML comments. Returns absolute path."""
        return MdExporter.export(renderable_doc, output_path)

    @staticmethod
    def export_pdf(renderable_doc: RenderableDocument, output_path: str) -> str:
        """Exports to PDF with absolute bbox positioning. Returns absolute path."""
        return PdfExporter.export(renderable_doc, output_path)

    @staticmethod
    def export_docx(renderable_doc: RenderableDocument, output_path: str) -> str:
        """Exports to DOCX with reading-order text and bbox metadata. Returns absolute path."""
        return DocxExporter.export(renderable_doc, output_path)
