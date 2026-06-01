# Intelligent Document Processing (IDP) Pipeline

An advanced, end-to-end Intelligent Document Processing (IDP) and OCR pipeline built with Python. This project takes raw document images (PDFs, scans) and reconstructs them into semantically structured, layout-aware digital formats (DOCX, PDF, Markdown, JSON) using state-of-the-art computer vision and spatial graph analysis.

## 🚀 Features
- **Spatial Geometry Engine**: Highly accurate layout detection using DocTR. Avoids simple "tight" OCR boxes in favor of collision-safe layout geometry.
- **Semantic Reconstruction**: Graph-based reconstruction engine that perfectly understands tables, multi-column layouts, headings, paragraphs, and key-value pairs based on vertical and horizontal spatial relationships.
- **Constraint Layout Solver**: Dynamically calculates typography rules (font sizes, wrapping, line heights) to recreate original visual structures during export.
- **Multi-Format Export**: Generates structurally sound DOCX files, absolute-coordinate PDFs, and structured JSON/Markdown.
- **Rich PyQt6 GUI**: A fully-featured desktop interface for pipeline orchestration, document structure inspection, and interactive visualization.

## 🧩 Architecture Modules
The pipeline is strictly decoupled into distinct functional modules:

- **M1 - Ingestion**: Document loading, queueing, and format standardization.
- **M2 - Preprocessing**: Deskewing, binarization, and image cleaning.
- **M3 - Layout Intelligence**: Spatial geometry detection, textline building, column detection, and collision safety engineering.
- **M4 - OCR Engine**: Text recognition via deep-learning backends (PaddleOCR, Tesseract) mapped to M3 geometries.
- **M5 - Semantic Graph Reconstructor**: Converts spatial nodes into human-readable semantic blocks (Tables, Lists, Headings).
- **M6 - Export Engine**: Layout-aware export to `PDF`, `DOCX`, `JSON`, and `Markdown`.
- **M7 - Orchestrator**: Manages state transitions, logging, and execution flows between modules.
- **M8 - GUI**: A PyQt6 interface featuring an ingestion queue, bbox overlay canvas, structure inspector, and real-time execution monitor.
- **M9 - Benchmarking**: Automated evaluation for Layout F1-Score, Word Error Rate (WER), and latency metrics.

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd se-intelligent-ocr-pipeline
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Running the Application

To launch the Interactive GUI (M8):

```bash
python -m src.pipeline.m8_gui.app
```

### Navigating the GUI
1. **Ingestion Queue (Left)**: Drag and drop files or add folders for processing. Select your preferred export format.
2. **Viewer Canvas (Center)**: Real-time visualization of document bounding boxes and layout overlays.
3. **Structure Inspector (Right)**: Tree-view representation of the reconstructed document (view tables, headings, and paragraphs).
4. **Monitor (Bottom)**: Real-time logs and batch progress tracking from the M7 Orchestrator.

## ⚙️ Configuration
Global configuration options, model selections, and threshold tunings can be edited interactively via the **Configuration** tab in the GUI or by editing the respective module `config.yaml` files.

## 📄 License
This project is licensed under the MIT License.
