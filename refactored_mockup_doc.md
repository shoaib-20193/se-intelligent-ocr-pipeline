# Intelligent Document Processing (IDP) Pipeline
## UI Mockup & System Evaluation Guide

**Target File:** `refactored_mockup.py`

This document provides a detailed breakdown of the `refactored_mockup.py` user interface. It is designed to help stakeholders, supervisors, and evaluation committees understand how the visual interface directly maps to the underlying architectural modules of the IDP and OCR Pipeline.

---

### 1. Design Philosophy: "One Page = One Mental Task"
The refactored UI was specifically designed to reduce cognitive overload. Document processing systems are inherently complex, involving file management, parameter tuning, and statistical evaluation. 

The application uses a **Tabbed Architecture** to strictly separate these three distinct workflows:
1.  **Document Processing** (Daily operation & human-in-the-loop review)
2.  **Configuration** (System tuning & parameter adjustments)
3.  **Benchmarking / Evaluation** (Research, metrics, and ground-truth validation)

The interface utilizes a "Dark Minimalist" theme to reduce eye strain during prolonged document review sessions and to make high-contrast overlay bounding boxes (e.g., Layout regions) pop out clearly to the user.

---

### 2. Workflow Breakdown & Module Mapping

#### Tab 1: Document Processing
This is the primary operational workspace. It maps to **Modules 1, 3, 5, and 7**.

*   **Top Action Bar:**
    *   **Pipeline Preset:** Allows users to quickly load macro-configurations (e.g., "Fast Draft" vs "High Accuracy") without manually tweaking individual parameters.
    *   **Start/Stop/Export:** Triggers the **Module 7 (Orchestration)** engine to process the queue.
*   **Left Panel (Ingestion & Queue):** Maps to **Module 1 (Document Ingestion)**.
    *   Features a drag-and-drop zone and a "Select Files..." button which dynamically populates the processing queue.
    *   Displays page counts and current status (e.g., queued, pending, ready).
*   **Center Panel (Visual Viewer):** Maps to **Module 3 (Layout Analysis)**.
    *   Allows users to inspect the document at various stages: Raw Image, Preprocessed (cleaned), Layout Overlay, and OCR Text.
    *   **The MockCanvas:** Visually demonstrates the AI's spatial understanding. Color-coded bounding boxes represent different detected semantic regions:
        *   Blue: Headings
        *   Green: Paragraphs
        *   Yellow/Amber: Tables
    *   UX toggles allow users to turn specific overlays on or off to reduce visual clutter.
*   **Right Panel (Structure Inspector):** Maps to **Module 5 (Text Refinement & Structural Reconstruction)**.
    *   Instead of dumping raw text, the system reconstructs a semantic "Document Structure Tree" (Headers, Paragraphs, Tables).
    *   The "Quick Edit TextBox" allows for human-in-the-loop validation, letting users click a detected region and manually correct any OCR hallucinations before finalizing.
*   **Bottom Panel (Orchestration Tracker):** Maps to **Module 7 (Pipeline Orchestration)**.
    *   **Stage Tracker:** Visually highlights which module is currently executing (Ingest ➔ Enhance ➔ Layout ➔ OCR ➔ Export).
    *   **Console:** Displays real-time, timestamped execution logs, providing transparency into the backend processes.

#### Tab 2: Configuration
This tab is decoupled from the main workspace so users aren't distracted by toggles while trying to read document text. It governs the rules of the pipeline.

*   **Ingestion (Module 1):** Limits on batch processing and allowed formats.
*   **Image Enhancement (Module 2):** Toggleable preprocessing steps like Denoising, Deskewing, and Adaptive Thresholding, which are critical for preparing low-quality scans for the OCR engine.
*   **Layout Detection (Module 3):** Allows swapping out the underlying AI model (e.g., LayoutLMv3 vs Detectron2) and setting confidence threshold cutoffs.
*   **OCR Engine (Module 4):** Exposes hardware acceleration toggles (GPU vs CPU) and language selection (English, Urdu, Arabic), directly interfacing with PaddleOCR settings.
*   **Post Processing (Module 5):** Rules for merging broken paragraphs, applying grammar correction, and structural refinement.
*   **Export Targets (Module 6):** Selectable output serializations (JSON, CSV, DOCX, XLSX) and an interactive folder browser to define where the structured data is saved.

#### Tab 3: Benchmarking / Evaluation
This tab transforms the application from a simple software tool into a **Research & Analytics Dashboard**, mapping entirely to **Module 9**.

*   **Target Dataset:** Allows the user to select standard research datasets (FUNSD, SROIE) or custom ground-truth sets to run the pipeline against.
*   **Key Evaluation Metrics:**
    *   **Precision, Recall, F1-Score:** Measures the accuracy of the spatial layout bounding boxes.
    *   **WER (Word Error Rate):** The standard metric for OCR text accuracy.
    *   **Latency & RAM:** Tracks the computational efficiency of the pipeline.
*   **Visualizations & Analytics:** Placeholders for rendering Confusion Matrix Heatmaps and isolating "Error Examples" (e.g., False Positives) to help researchers understand *where* the model is failing.
*   **Evaluation Logs:** A dedicated console specifically for granular benchmarking processes (e.g., calculating Levenshtein Distances, IoU comparisons).

---

### 3. Interactive Simulation Details
For evaluation purposes, the `refactored_mockup.py` script includes an active simulation to demonstrate how the UI reacts during live processing:

1.  Navigate to the **Document Processing** tab.
2.  Click **"Select Files..."** and choose dummy files to add to the queue.
3.  Click **"▶ Start Pipeline"**. 
4.  Observe the **Stage Tracker** at the bottom of the screen sequentially advancing through the pipeline stages (Ingest ➔ Enhance ➔ Layout ➔ OCR...), simulating backend processing time.
5.  Observe the **Bottom Console** actively outputting timestamped logs generated by the simulated Orchestration module.
