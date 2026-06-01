"""
src/pipeline/m8_gui/components/orchestrator_monitor.py
Displays M7 pipeline logs, state transitions, and progress bars.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt

class OrchestratorMonitor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Dashboard header
        header_layout = QHBoxLayout()
        
        # Module status indicators (stubbed visually)
        self.lbl_status = QLabel("M1-M7 Health: OK")
        self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Batch Progress Bar
        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setValue(0)
        self.batch_progress.setFormat("Batch Progress: %v/%m files")
        
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()
        header_layout.addWidget(self.batch_progress, stretch=1)
        
        # Log view
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.text_edit)
        
    def append_log(self, message: str):
        self.text_edit.append(message)
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_batch_progress(self, current: int, total: int):
        self.batch_progress.setMaximum(total)
        self.batch_progress.setValue(current)
        if current == total and total > 0:
            self.lbl_status.setText("M1-M7 Health: IDLE (Complete)")
            self.lbl_status.setStyleSheet("color: #2196F3; font-weight: bold;")
        elif total > 0:
            self.lbl_status.setText("M1-M7 Health: RUNNING")
            self.lbl_status.setStyleSheet("color: #FFC107; font-weight: bold;")
