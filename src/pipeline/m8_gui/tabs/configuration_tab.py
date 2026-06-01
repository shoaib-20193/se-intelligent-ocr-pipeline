"""
src/pipeline/m8_gui/tabs/configuration_tab.py
Read-only UI configuration reference with placeholder controls.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QComboBox, QCheckBox, QPushButton, QHBoxLayout, QScrollArea
)
from PyQt6.QtCore import Qt

class ConfigurationTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        
        lbl = QLabel("System Configuration (Placeholder UI)")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(lbl)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # M1 Ingestion Settings
        m1_group = QGroupBox("M1 Ingestion Settings")
        m1_layout = QFormLayout()
        
        dpi_combo = QComboBox()
        dpi_combo.addItems(["300 DPI", "150 DPI", "600 DPI", "Auto-detect"])
        m1_layout.addRow("Target DPI:", dpi_combo)
        
        m1_layout.addRow("Auto-rotate pages:", QCheckBox("Enabled"))
        m1_layout.addRow("Deskew images:", QCheckBox("Enabled"))
        m1_group.setLayout(m1_layout)
        layout.addWidget(m1_group)
        
        # M3 Layout Model Selection
        m3_group = QGroupBox("M3 Layout Model Selection")
        m3_layout = QFormLayout()
        
        model_combo = QComboBox()
        model_combo.addItems(["DocTR db_resnet50 (Default)", "PaddleX RT-DETR", "LayoutLMv3", "Fast R-CNN"])
        m3_layout.addRow("Detection Model:", model_combo)
        
        confidence_combo = QComboBox()
        confidence_combo.addItems(["0.5 (Standard)", "0.3 (Aggressive)", "0.7 (Strict)"])
        m3_layout.addRow("Confidence Threshold:", confidence_combo)
        m3_group.setLayout(m3_layout)
        layout.addWidget(m3_group)
        
        # M4 OCR Engine Config
        m4_group = QGroupBox("M4 OCR Engine Config")
        m4_layout = QFormLayout()
        
        ocr_combo = QComboBox()
        ocr_combo.addItems(["PaddleOCR 2.7.3 (Stable)", "Tesseract 5", "EasyOCR"])
        m4_layout.addRow("OCR Backend:", ocr_combo)
        
        m4_layout.addRow("Enable Dictionary Correction:", QCheckBox("Enabled (English)"))
        m4_layout.addRow("Force CPU Execution:", QCheckBox("Enabled (Safe Mode)"))
        m4_group.setLayout(m4_layout)
        layout.addWidget(m4_group)
        
        # M6 Export Format Toggles
        m6_group = QGroupBox("M6 Export Formats")
        m6_layout = QVBoxLayout()
        m6_layout.addWidget(QCheckBox("PDF (Rendered absolute coordinates)"))
        m6_layout.addWidget(QCheckBox("DOCX (Flowing text layout)"))
        m6_layout.addWidget(QCheckBox("JSON (Structured representation)"))
        m6_layout.addWidget(QCheckBox("Markdown (Semantic text)"))
        m6_group.setLayout(m6_layout)
        layout.addWidget(m6_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Bottom action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setDisabled(True)
        save_btn = QPushButton("Apply Configuration")
        save_btn.setDisabled(True)
        save_btn.setStyleSheet("background-color: #007acc; color: white; padding: 5px 15px;")
        
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)
