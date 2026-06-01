"""
src/pipeline/m8_gui/components/structure_inspector.py
Read-only hierarchical tree view of the RenderableDocument.
Shows block-level structure from the Document Reconstruction Engine.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QTextEdit, QSplitter
)
from PyQt6.QtCore import pyqtSignal, Qt
from src.pipeline.m6_export.contracts import RenderableDocument

class StructureInspector(QWidget):
    block_selected = pyqtSignal(str)  # Emits token_id

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Document Structure (Block-Level)")
        self.tree.itemClicked.connect(self._on_item_clicked)

        self.metadata_panel = QTextEdit()
        self.metadata_panel.setReadOnly(True)
        self.metadata_panel.setPlaceholderText("Select a block to view metadata...")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.tree)

        meta_container = QWidget()
        meta_layout = QVBoxLayout(meta_container)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_lbl = QLabel("Block Metadata:")
        meta_layout.addWidget(meta_lbl)
        meta_layout.addWidget(self.metadata_panel)

        splitter.addWidget(meta_container)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

        self.current_document = None
        self.token_data_map = {}

    def load_renderable_document(self, doc: RenderableDocument):
        self.tree.clear()
        self.metadata_panel.clear()
        self.token_data_map.clear()
        self.current_document = doc

        if not doc.pages:
            return

        root = QTreeWidgetItem(self.tree, [f"Document {doc.document_id}"])
        root.setExpanded(True)

        for page in doc.pages:
            cols_str = f" ({page.num_columns} col)" if page.num_columns > 1 else ""
            page_node = QTreeWidgetItem(root, [f"Page {page.page_number}{cols_str}"])
            page_node.setExpanded(True)

            # Group blocks by type
            type_nodes = {}

            for token in sorted(page.tokens, key=lambda t: t.reading_order):
                b_type = token.block_type.upper()
                if b_type not in type_nodes:
                    tn = QTreeWidgetItem(page_node, [b_type])
                    tn.setExpanded(True)
                    type_nodes[b_type] = tn

                self.token_data_map[token.token_id] = token

                preview = token.text[:50] + "..." if len(token.text) > 50 else token.text
                preview = preview.replace("\n", " ↵ ")
                item = QTreeWidgetItem(type_nodes[b_type], [f"[{token.reading_order}] {preview}"])
                item.setData(0, Qt.ItemDataRole.UserRole, token.token_id)

    def _on_item_clicked(self, item, column):
        token_id = item.data(0, Qt.ItemDataRole.UserRole)
        if token_id and token_id in self.token_data_map:
            token = self.token_data_map[token_id]
            self.block_selected.emit(token_id)

            meta_text = (
                f"Block ID: {token.token_id}\n"
                f"Type: {token.block_type.upper()}\n"
                f"Confidence: {token.confidence:.2f}\n"
                f"Reading Order: {token.reading_order}\n"
                f"Column: {token.column_id}\n"
                f"Bounds (x,y,w,h): ({token.x:.1f}, {token.y:.1f}, {token.width:.1f}, {token.height:.1f})\n"
                f"Page Space: {token.page_width:.0f} x {token.page_height:.0f}\n"
                f"Source Regions: {', '.join(token.source_region_ids)}\n"
                f"─────────────────────\n"
                f"Text:\n{token.text}"
            )
            self.metadata_panel.setPlainText(meta_text)
