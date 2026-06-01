"""
src/pipeline/m8_gui/main_window.py
Defines the main QMainWindow and its tabbed layout.
"""
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from src.pipeline.m8_gui.tabs.processing_tab import ProcessingTab
from src.pipeline.m8_gui.tabs.configuration_tab import ConfigurationTab
from src.pipeline.m8_gui.tabs.benchmarking_tab import BenchmarkingTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M8 PyQt6 Intelligent Document Processing")
        self.resize(1200, 800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Initialize Tabs
        self.processing_tab = ProcessingTab()
        self.configuration_tab = ConfigurationTab()
        self.benchmarking_tab = BenchmarkingTab()
        
        self.tabs.addTab(self.processing_tab, "Document Processing")
        self.tabs.addTab(self.configuration_tab, "Configuration")
        self.tabs.addTab(self.benchmarking_tab, "Benchmarking")
