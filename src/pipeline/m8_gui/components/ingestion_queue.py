"""
src/pipeline/m8_gui/components/ingestion_queue.py
Advanced file ingestion component with multi-file, folder scanning, and status tracking.
Includes export panel with file name input, format selector, and directory picker.
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QFileDialog, QHeaderView, QCheckBox,
    QLineEdit, QComboBox, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class IngestionQueue(QWidget):
    # Signals emitted when queue changes or execution starts
    files_added = pyqtSignal(list)
    start_batch_requested = pyqtSignal()
    stop_batch_requested = pyqtSignal()
    export_requested = pyqtSignal(str, str, str)  # format, filename, output_dir
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Toolbar for adding files
        toolbar = QHBoxLayout()
        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_remove = QPushButton("Remove Selected")
        self.check_recursive = QCheckBox("Recursive Scan")
        
        toolbar.addWidget(self.btn_add_files)
        toolbar.addWidget(self.btn_add_folder)
        toolbar.addWidget(self.check_recursive)
        toolbar.addWidget(self.btn_remove)
        
        # Execution controls
        exec_toolbar = QHBoxLayout()
        self.btn_run = QPushButton("Start Batch")
        self.btn_stop = QPushButton("Stop/Cancel")
        self.btn_retry = QPushButton("Retry Failed")
        
        exec_toolbar.addWidget(self.btn_run)
        exec_toolbar.addWidget(self.btn_stop)
        exec_toolbar.addWidget(self.btn_retry)
        
        # ======== EXPORT PANEL ========
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        # Row 1: File name input
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("File Name:"))
        self.export_filename = QLineEdit()
        self.export_filename.setPlaceholderText("exported_document")
        name_row.addWidget(self.export_filename)
        export_layout.addLayout(name_row)
        
        # Row 2: Output directory
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Output Dir:"))
        self.export_dir_label = QLineEdit()
        self.export_dir_label.setPlaceholderText("Select output directory...")
        self.export_dir_label.setReadOnly(True)
        self.btn_browse_dir = QPushButton("Browse...")
        self.btn_browse_dir.clicked.connect(self._browse_export_dir)
        dir_row.addWidget(self.export_dir_label)
        dir_row.addWidget(self.btn_browse_dir)
        export_layout.addLayout(dir_row)
        
        # Row 3: Format selector + Export button
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self.export_format = QComboBox()
        self.export_format.addItems(["JSON", "TXT", "Markdown", "PDF", "Word (DOCX)"])
        format_row.addWidget(self.export_format)
        
        self.btn_export = QPushButton("Export Current")
        self.btn_export.clicked.connect(self._emit_export)
        format_row.addWidget(self.btn_export)
        export_layout.addLayout(format_row)
        
        # Queue Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["File Name", "Status", "Progress"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        layout.addLayout(exec_toolbar)
        layout.addWidget(export_group)
        
        # Connections
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_remove.clicked.connect(self._remove_selected)
        
        self.btn_run.clicked.connect(self.start_batch_requested.emit)
        self.btn_stop.clicked.connect(self.stop_batch_requested.emit)

        # Internal state
        self.file_paths = []
        self._export_dir = ""
        
    def _browse_export_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if folder:
            self._export_dir = folder
            self.export_dir_label.setText(folder)
    
    def _emit_export(self):
        """Emit export signal with format, filename, and output directory."""
        format_map = {
            "JSON": "json",
            "TXT": "txt",
            "Markdown": "md",
            "PDF": "pdf",
            "Word (DOCX)": "docx"
        }
        fmt = format_map.get(self.export_format.currentText(), "json")
        filename = self.export_filename.text().strip() or "exported_document"
        output_dir = self._export_dir or "."
        self.export_requested.emit(fmt, filename, output_dir)
        
    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", "Documents (*.pdf *.png *.jpg *.jpeg *.tiff)"
        )
        if files:
            self._enqueue_files(files)
            
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            files_to_add = []
            recursive = self.check_recursive.isChecked()
            valid_exts = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}
            
            if recursive:
                for root, _, files in os.walk(folder):
                    for f in files:
                        if Path(f).suffix.lower() in valid_exts:
                            files_to_add.append(os.path.join(root, f))
            else:
                for f in os.listdir(folder):
                    path = os.path.join(folder, f)
                    if os.path.isfile(path) and Path(f).suffix.lower() in valid_exts:
                        files_to_add.append(path)
                        
            self._enqueue_files(files_to_add)
            
    def _enqueue_files(self, new_files):
        for f in new_files:
            if f not in self.file_paths:
                self.file_paths.append(f)
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(Path(f).name))
                self.table.setItem(row, 1, QTableWidgetItem("QUEUED"))
                self.table.setItem(row, 2, QTableWidgetItem("0%"))
        self.files_added.emit(self.file_paths)
        
    def _remove_selected(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.file_paths.pop(row)
            self.table.removeRow(row)
        self.files_added.emit(self.file_paths)
        
    def update_file_status(self, file_index: int, status: str, progress: str = None):
        if 0 <= file_index < self.table.rowCount():
            self.table.setItem(file_index, 1, QTableWidgetItem(status))
            if progress is not None:
                self.table.setItem(file_index, 2, QTableWidgetItem(progress))
