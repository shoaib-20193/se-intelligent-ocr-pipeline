"""
Real Document Loader — loads PDFs and images directly into PreprocessedDocument DTOs.
"""
import logging
from pathlib import Path
import numpy as np

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

from src.data_model.document import DocumentMetadata
from src.data_model.preprocessed import PreprocessedDocument, ProcessedPage

logger = logging.getLogger(__name__)

def load_real_document(file_path: Path) -> PreprocessedDocument:
    """
    Loads a PDF or image from disk and constructs a dummy PreprocessedDocument
    suitable for feeding into the M3 pipeline.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot load document, file not found: {file_path}")
        
    ext = file_path.suffix.lower()
    pages = []
    
    if ext == ".pdf":
        if not _PDF_AVAILABLE:
            raise ImportError("pdf2image is required to load PDF documents.")
        try:
            pil_images = convert_from_path(str(file_path))
            for i, img in enumerate(pil_images, start=1):
                cv_img = np.array(img)
                # Convert RGB (from PIL) to BGR (standard for cv2/M2 outputs)
                if len(cv_img.shape) == 3 and cv_img.shape[2] == 3:
                    cv_img = cv_img[:, :, ::-1].copy()
                pages.append(ProcessedPage(page_number=i, clean_image=cv_img))
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF {file_path}: {e}")
            
    elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        if not _CV2_AVAILABLE:
            raise ImportError("OpenCV (cv2) is required to load images.")
        try:
            # imread reads as BGR
            cv_img = cv2.imread(str(file_path))
            if cv_img is None:
                raise ValueError(f"cv2.imread returned None. Corrupt or unreadable image: {file_path}")
            pages.append(ProcessedPage(page_number=1, clean_image=cv_img))
        except Exception as e:
            raise RuntimeError(f"Failed to read image {file_path}: {e}")
    else:
        raise ValueError(f"Unsupported document format: {ext}")
        
    if not pages:
        raise ValueError(f"Document {file_path} contained no readable pages.")
        
    h, w = pages[0].clean_image.shape[:2]
    
    meta = DocumentMetadata(
        filename=file_path.name,
        file_size=file_path.stat().st_size,
        page_count=len(pages),
        resolution=(w, h)
    )
    
    return PreprocessedDocument(metadata=meta, pages=pages)
