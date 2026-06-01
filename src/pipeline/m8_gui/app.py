"""
src/pipeline/m8_gui/app.py
Primary entry point for the M8 PyQt6 GUI.
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication
from src.pipeline.m8_gui.main_window import MainWindow

# Configure logging for M8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def perform_preflight_checks():
    """
    Validates the runtime environment before launching the GUI.
    Fails fast if critical dependencies are missing.
    """
    required_packages = ["PyQt6", "numpy"]
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            error_msg = f"Critical Preflight Failure: Missing required package '{pkg}'."
            logger.error(error_msg)
            print(error_msg)
            sys.exit(1)

def launch_gui():
    """
    Launches the strictly passive rendering M8 GUI.
    """
    perform_preflight_checks()
    app = QApplication(sys.argv)
    
    # Dark minimalist styling
    app.setStyle("Fusion")
    dark_palette = """
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            padding: 8px 16px;
            margin-right: 2px;
            color: #d4d4d4;
        }
        QTabBar::tab:selected {
            background-color: #3e3e42;
            border-bottom: 2px solid #007acc;
        }
        QGraphicsView {
            background-color: #252526;
            border: none;
        }
        QTreeView, QListWidget, QTextEdit {
            background-color: #252526;
            border: 1px solid #3e3e42;
        }
        QPushButton {
            background-color: #0e639c;
            color: white;
            border: none;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #1177bb;
        }
        QPushButton:disabled {
            background-color: #4d4d4d;
            color: #a0a0a0;
        }
    """
    app.setStyleSheet(dark_palette)
    
    window = MainWindow()
    window.show()
    
    logger.info("M8 GUI initialized successfully.")
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_gui()
