"""
M1 — Document Ingestion interface [V1 — Real file validation + metadata extraction]
Image rendering deferred to V2 (requires OpenCV).
See agents.md §MODULE_CONTRACTS → M1
"""
from __future__ import annotations
import os
import uuid
import logging
import fitz
import numpy as np
import cv2

logger = logging.getLogger(__name__)

from src.data_model.request import ProcessingRequest
from src.data_model.document import Document, DocumentMetadata, RawPage
from src.pipeline.m1_ingest.validator import (
    validate_readable, validate_extension, validate_file_size, validate_page_count
)


def _rasterize_pdf(path: str) -> list[np.ndarray]:
    """Rasterize PDF pages into numpy arrays using PyMuPDF (fitz)."""
    try:
        doc = fitz.open(path)
        page_count = len(doc)
        if page_count == 0:
            raise ValueError("PDF contains no pages.")
            
        images = []
        for i in range(page_count):
            page = doc[i]
            pix = page.get_pixmap(alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Ensure it is a 3-channel image (OpenCV standard is BGR)
            if pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                
            images.append(img)
            
        return images
    except Exception as e:
        logger.error(f"PDF rasterization failed: {e}")
        raise ValueError(f"Failed to rasterize PDF: {e}")

def _load_image(path: str) -> list[np.ndarray]:
    """Load a single image file into a list of one numpy array."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to rasterize image file: {path}")
    return [img]


def ingest(request: ProcessingRequest) -> Document:
    """
    V1 — Real file validation + metadata extraction. No image rendering yet.
    Input:  ProcessingRequest
    Output: Document
    Raises: ValidationError (caught by M7 at document boundary)
    """
    path = request.input_path

    # Steps 1–4: validate (agents.md §MODULE_CONTRACTS → M1)
    validate_readable(path)
    validate_extension(path)
    validate_file_size(path, request.constraints.max_file_size_mb)

    ext = os.path.splitext(path)[1].lower()
    file_size = os.path.getsize(path)

    # Steps 5-6: page count & image loading
    if ext == ".pdf":
        images = _rasterize_pdf(path)
    else:
        images = _load_image(path)
        
    page_count = len(images)
    
    # Validation_Guards: Add runtime log: number of rasterized pages vs PDF page count
    logger.info(f"[M1_INGEST] Rasterized {page_count} pages from {path}")
    if page_count == 0:
        raise ValueError("Rasterization produced 0 pages. Failing fast.")

    # Step 3 (page limit check)
    validate_page_count(page_count, request.constraints.max_pages)

    # Steps 7–9: metadata + normalise
    document_id = str(uuid.uuid4())
    
    h, w = images[0].shape[:2]
    metadata = DocumentMetadata(
        filename=os.path.basename(path),
        file_size=file_size,
        page_count=page_count,
        resolution=(w, h),
    )

    # Step 10: pages
    pages = []
    for i in range(page_count):
        img = images[i]
        
        # Validation_Guards: Add assertion in M1: page.image is not None and isinstance(np.ndarray)
        assert img is not None and isinstance(img, np.ndarray), f"Page {i+1} rasterization failed or invalid type"
        
        pages.append(RawPage(page_number=i + 1, image=img))

    return Document(document_id=document_id, metadata=metadata, pages=pages)
