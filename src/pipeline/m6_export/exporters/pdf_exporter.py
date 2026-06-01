"""
src/pipeline/m6_export/exporters/pdf_exporter.py
Exports RenderableDocument to PDF with absolute bbox positioning.
Block-level rendering: headings centered, tables as grids, paragraphs wrapped.
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

from src.pipeline.m6_export.contracts import RenderableDocument


class PdfExporter:
    @staticmethod
    def export(document: RenderableDocument, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(path), pagesize=letter)

        for page in document.pages:
            c.setPageSize((page.width, page.height))

            for token in sorted(page.tokens, key=lambda t: t.reading_order):
                b_type = token.block_type.lower()
                font_size = token.font_size if token.font_size > 0 else 10

                if b_type == "heading":
                    PdfExporter._draw_heading(c, token, page.height, font_size)
                elif b_type == "table":
                    PdfExporter._draw_table(c, token, page.height)
                else:
                    PdfExporter._draw_text_block(c, token, page.height, font_size, b_type)

            c.showPage()

        c.save()
        return str(path.absolute())

    @staticmethod
    def _draw_heading(c, token, page_height, font_size):
        """Centered bold heading."""
        c.setFont("Helvetica-Bold", font_size)
        y_pdf = page_height - token.y - token.height
        # Center text within bbox width
        text_width = c.stringWidth(token.text, "Helvetica-Bold", font_size)
        x_centered = token.x + (token.width - text_width) / 2.0
        c.drawString(max(x_centered, token.x), y_pdf, token.text)

    @staticmethod
    def _draw_table(c, token, page_height):
        """Render table as grid with cell borders."""
        table_rows = token.spatial_metadata.get("table_rows")
        
        if table_rows:
            if not table_rows:
                return
            num_rows = len(table_rows)
            row_height = max(token.height / max(num_rows, 1), 14)

            for row_idx, cells in enumerate(table_rows):
                cell_width = token.width / max(len(cells), 1)
                for col_idx, cell_text in enumerate(cells):
                    cell_x = token.x + col_idx * cell_width
                    cell_y_top = token.y + row_idx * row_height
                    cell_y_pdf = page_height - cell_y_top - row_height

                    # Draw cell border
                    c.setStrokeColorRGB(0.7, 0.7, 0.7)
                    c.rect(cell_x, cell_y_pdf, cell_width, row_height, stroke=1, fill=0)

                    # Draw cell text
                    font_name = "Helvetica-Bold" if row_idx == 0 else "Helvetica"
                    c.setFont(font_name, 9)
                    c.drawString(cell_x + 2, cell_y_pdf + 3, cell_text.strip()[:40])
        else:
            # Fallback
            lines = token.text.split("\n")
            if not lines:
                return

            row_height = max(token.height / max(len(lines), 1), 14)

            for row_idx, line in enumerate(lines):
                cells = line.split(" | ")
                cell_width = token.width / max(len(cells), 1)

                for col_idx, cell_text in enumerate(cells):
                    cell_x = token.x + col_idx * cell_width
                    cell_y_top = token.y + row_idx * row_height
                    cell_y_pdf = page_height - cell_y_top - row_height

                    # Draw cell border
                    c.setStrokeColorRGB(0.7, 0.7, 0.7)
                    c.rect(cell_x, cell_y_pdf, cell_width, row_height, stroke=1, fill=0)

                    # Draw cell text
                    font_name = "Helvetica-Bold" if row_idx == 0 else "Helvetica"
                    c.setFont(font_name, 9)
                    c.drawString(cell_x + 2, cell_y_pdf + 3, cell_text.strip()[:40])

    @staticmethod
    def _draw_text_block(c, token, page_height, font_size, b_type):
        """Render paragraph/list/kv as wrapped text inside bbox."""
        font_name = "Helvetica"
        c.setFont(font_name, font_size)

        # Split text into lines that fit within bbox width
        available_width = max(token.width - 4, 50)
        wrapped_lines = simpleSplit(token.text, font_name, font_size, available_width)

        y_pdf = page_height - token.y - font_size - 2
        line_height = font_size + 2

        for line in wrapped_lines:
            c.drawString(token.x + 2, y_pdf, line)
            y_pdf -= line_height
