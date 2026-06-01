"""
src/pipeline/m8_gui/tabs/benchmarking_tab.py
Evaluation dashboard placeholder with mock UI elements.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout, 
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)

class BenchmarkingTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        lbl = QLabel("Benchmarking & Analytics Dashboard")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(lbl)
        
        header_layout.addStretch()
        
        dataset_combo = QComboBox()
        dataset_combo.addItems(["FUNSD Dataset", "DocVQA", "Custom Set A"])
        header_layout.addWidget(QLabel("Evaluation Dataset:"))
        header_layout.addWidget(dataset_combo)
        
        run_btn = QPushButton("Run Evaluation")
        run_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        run_btn.setDisabled(True)
        header_layout.addWidget(run_btn)
        
        layout.addLayout(header_layout)
        
        # Overall Progress
        progress_group = QGroupBox("Evaluation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Awaiting execution... 0%")
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Metrics Table
        metrics_group = QGroupBox("Key Performance Indicators (M9 Placeholder)")
        metrics_layout = QVBoxLayout()
        
        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["Metric", "Current Score", "Target baseline"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        metrics = [
            ("Layout F1-Score (M3)", "N/A", "> 0.90"),
            ("OCR Word Error Rate (M4)", "N/A", "< 0.05"),
            ("Semantic Graph Accuracy (M5)", "N/A", "> 0.85"),
            ("E2E Pipeline Latency (ms/page)", "N/A", "< 1500 ms")
        ]
        
        for i, (metric, current, target) in enumerate(metrics):
            self.table.setItem(i, 0, QTableWidgetItem(metric))
            self.table.setItem(i, 1, QTableWidgetItem(current))
            self.table.setItem(i, 2, QTableWidgetItem(target))
            
        metrics_layout.addWidget(self.table)
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Export Actions
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_btn = QPushButton("Export Metrics Report (.csv)")
        export_btn.setDisabled(True)
        export_layout.addWidget(export_btn)
        layout.addLayout(export_layout)
        
        layout.addStretch()
