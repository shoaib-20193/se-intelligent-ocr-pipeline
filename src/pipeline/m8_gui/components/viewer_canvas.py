"""
src/pipeline/m8_gui/components/viewer_canvas.py
M8 Document Viewer — block-level renderer.
Renders DocumentBlocks (not fragments) using bbox-driven absolute positioning.

Block rendering rules:
    - heading: centered text, bold, colored bbox overlay
    - paragraph: left-aligned text, wrapped inside bbox width
    - table: grid lines drawn, pipe-separated row text
    - key_value_pair: compact left-aligned with subtle background
    - list: left-aligned, preserving bullet/number prefixes

RULE: Position comes ONLY from bbox. NEVER from text layout engine.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsTextItem, QGraphicsRectItem
)
from PyQt6.QtGui import QFont, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal
from src.pipeline.m6_export.contracts import RenderableDocument

# Block-type → bbox overlay color
BLOCK_TYPE_COLORS = {
    "heading": "#e74c3c",
    "paragraph": "#007acc",
    "list": "#2ecc71",
    "table": "#f39c12",
    "key_value_pair": "#9b59b6",
    "unknown": "#95a5a6"
}

# Block-type → background fill alpha
BLOCK_TYPE_FILL_ALPHA = {
    "heading": 20,
    "paragraph": 8,
    "list": 10,
    "table": 15,
    "key_value_pair": 12,
    "unknown": 5
}


class ViewerCanvas(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(
            self.view.renderHints()
        )
        layout.addWidget(self.view)

        self.current_document = None
        self.block_items = {}  # token_id → QGraphicsRectItem

    def load_renderable_document(self, doc: RenderableDocument):
        """Load and render a RenderableDocument at block level."""
        self.scene.clear()
        self.block_items.clear()
        self.current_document = doc

        if not doc.pages:
            return

        y_offset = 0.0
        page_gap = 30.0

        for page in doc.pages:
            # Draw page background
            page_bg = self.scene.addRect(
                0, y_offset, page.width, page.height,
                QPen(QColor("#cccccc")),
                QBrush(QColor("#ffffff"))
            )

            # Render each block (NOT token-level fragments)
            for token in sorted(page.tokens, key=lambda t: t.reading_order):
                self._render_block(token, y_offset, page)

            y_offset += page.height + page_gap

        # Fit the view to all content
        self.view.setSceneRect(self.scene.itemsBoundingRect())

    def _render_block(self, token, y_offset: float, page):
        """Render a single DocumentBlock according to its type."""
        b_type = token.block_type.lower()
        color_hex = BLOCK_TYPE_COLORS.get(b_type, BLOCK_TYPE_COLORS["unknown"])
        fill_alpha = BLOCK_TYPE_FILL_ALPHA.get(b_type, 5)

        bx = token.x
        by = token.y + y_offset
        bw = max(token.width, 20)
        bh = max(token.height, 15)

        # ── Draw bbox overlay ──
        border_color = QColor(color_hex)
        border_color.setAlpha(120)
        fill_color = QColor(color_hex)
        fill_color.setAlpha(fill_alpha)

        rect_item = self.scene.addRect(
            bx, by, bw, bh,
            QPen(border_color, 1.0),
            QBrush(fill_color)
        )
        self.block_items[token.token_id] = rect_item

        # ── Block type label (small tag in top-left) ──
        tag = QGraphicsTextItem(b_type.upper())
        tag_font = QFont("Segoe UI", 6)
        tag.setFont(tag_font)
        tag.setDefaultTextColor(QColor(color_hex))
        tag.setPos(bx, by - 10)
        self.scene.addItem(tag)

        # ── Render text based on block type ──
        if b_type == "heading":
            self._render_heading(token, bx, by, bw, bh)
        elif b_type == "table":
            self._render_table(token, bx, by, bw, bh)
        elif b_type == "key_value_pair":
            self._render_kv(token, bx, by, bw, bh)
        else:
            # paragraph, list, unknown
            self._render_text_block(token, bx, by, bw, bh)

    def _apply_dynamic_styling(self, text_item: QGraphicsTextItem, token, w: float):
        """Applies solved layout from M6.5."""
        font = QFont("Segoe UI", int(token.font_size))
        if token.font_weight >= 600:
            font.setBold(True)
        text_item.setFont(font)
        
        wrap_mode = token.spatial_metadata.get("wrap_mode", "soft_wrap")
        if wrap_mode == "soft_wrap":
            text_item.setTextWidth(w)
            
        doc = text_item.document()
        cursor_option = doc.defaultTextOption()
        
        alignment = token.alignment
        if alignment == "center":
            cursor_option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif alignment == "right":
            cursor_option.setAlignment(Qt.AlignmentFlag.AlignRight)
        elif alignment == "justify":
            cursor_option.setAlignment(Qt.AlignmentFlag.AlignJustify)
        else:
            cursor_option.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        doc.setDefaultTextOption(cursor_option)

    def _render_heading(self, token, x, y, w, h):
        """Render heading dynamically solved."""
        text_item = QGraphicsTextItem(token.text)
        self._apply_dynamic_styling(text_item, token, w)
        text_item.setDefaultTextColor(QColor("#1a1a1a"))
        text_item.setPos(x, y)
        self.scene.addItem(text_item)

    def _render_table(self, token, x, y, w, h):
        """Render table: pipe-separated rows with grid lines."""
        table_rows = token.spatial_metadata.get("table_rows")
        font_size = int(token.font_size)
        
        if table_rows:
            num_rows = len(table_rows)
            row_height = h / max(num_rows, 1)

            for row_idx, cells in enumerate(table_rows):
                cell_width = w / max(len(cells), 1)

                for col_idx, cell_text in enumerate(cells):
                    cell_x = x + col_idx * cell_width
                    cell_y = y + row_idx * row_height

                    # Cell border
                    self.scene.addRect(
                        cell_x, cell_y, cell_width, row_height,
                        QPen(QColor("#d4a017"), 0.5),
                        QBrush(Qt.BrushStyle.NoBrush)
                    )

                    # Cell text
                    text_item = QGraphicsTextItem(cell_text.strip())
                    font = QFont("Consolas", font_size)
                    if row_idx == 0:
                        font.setBold(True)  # First row = header
                    text_item.setFont(font)
                    text_item.setDefaultTextColor(QColor("#2c2c2c"))
                    
                    wrap_mode = token.spatial_metadata.get("wrap_mode", "soft_wrap")
                    if wrap_mode == "soft_wrap":
                        text_item.setTextWidth(cell_width - 4)
                        
                    text_item.setPos(cell_x + 2, cell_y + 1)
                    self.scene.addItem(text_item)
        else:
            # Fallback
            lines = token.text.split("\n")
            if not lines:
                return

            row_height = h / max(len(lines), 1)

            for row_idx, line in enumerate(lines):
                cells = line.split(" | ")
                cell_width = w / max(len(cells), 1)

                for col_idx, cell_text in enumerate(cells):
                    cell_x = x + col_idx * cell_width
                    cell_y = y + row_idx * row_height

                    # Cell border
                    self.scene.addRect(
                        cell_x, cell_y, cell_width, row_height,
                        QPen(QColor("#d4a017"), 0.5),
                        QBrush(Qt.BrushStyle.NoBrush)
                    )

                    # Cell text
                    text_item = QGraphicsTextItem(cell_text.strip())
                    font = QFont("Consolas", font_size)
                    if row_idx == 0:
                        font.setBold(True)  # First row = header
                    text_item.setFont(font)
                    text_item.setDefaultTextColor(QColor("#2c2c2c"))
                    
                    wrap_mode = token.spatial_metadata.get("wrap_mode", "soft_wrap")
                    if wrap_mode == "soft_wrap":
                        text_item.setTextWidth(cell_width - 4)
                        
                    text_item.setPos(cell_x + 2, cell_y + 1)
                    self.scene.addItem(text_item)

    def _render_kv(self, token, x, y, w, h):
        """Render key-value pairs."""
        text_item = QGraphicsTextItem(token.text)
        self._apply_dynamic_styling(text_item, token, w)
        text_item.setDefaultTextColor(QColor("#4a4a4a"))
        text_item.setPos(x, y)
        self.scene.addItem(text_item)

    def _render_text_block(self, token, x, y, w, h):
        """Render paragraph/list/unknown."""
        text_item = QGraphicsTextItem(token.text)
        self._apply_dynamic_styling(text_item, token, w)
        text_item.setDefaultTextColor(QColor("#2c2c2c"))
        text_item.setPos(x, y)
        self.scene.addItem(text_item)

    def highlight_block(self, token_id: str):
        """Highlight a specific block by its token_id."""
        # Reset all
        for tid, rect in self.block_items.items():
            b_type = "unknown"
            if self.current_document:
                for page in self.current_document.pages:
                    for t in page.tokens:
                        if t.token_id == tid:
                            b_type = t.block_type
                            break
            color = QColor(BLOCK_TYPE_COLORS.get(b_type, "#95a5a6"))
            color.setAlpha(BLOCK_TYPE_FILL_ALPHA.get(b_type, 5))
            rect.setBrush(QBrush(color))

        # Highlight selected
        if token_id in self.block_items:
            highlight = QColor("#ffff00")
            highlight.setAlpha(60)
            self.block_items[token_id].setBrush(QBrush(highlight))
