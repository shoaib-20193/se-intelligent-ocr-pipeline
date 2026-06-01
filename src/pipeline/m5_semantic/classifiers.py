"""
src/pipeline/m5_semantic/classifiers.py
Implements heuristic-only classification rules for OCR regions.
No AI, NLP, or deep learning models are used here.
"""

def classify_block(text: str) -> str:
    """
    Categorizes raw text into one of 4 allowed semantic types:
    'heading', 'list', 'paragraph', 'unknown'.
    """
    clean_text = text.strip()
    if not clean_text:
        return "unknown"
        
    # Rule 1: Heading
    if len(clean_text) < 60 and clean_text.isupper():
        return "heading"
        
    # Rule 2: List item
    if clean_text.startswith(("•", "-", "*")):
        return "list"
        
    # Rule 3: Paragraph
    if len(clean_text.split()) > 5:
        return "paragraph"
        
    # Rule 4: Fallback
    return "unknown"
