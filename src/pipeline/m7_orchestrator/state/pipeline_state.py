from enum import Enum, auto

class PipelineState(Enum):
    """
    Deterministic states of the document processing pipeline.
    """
    INITIALIZED = auto()
    LOADED = auto()
    PREPROCESSED = auto()
    LAYOUT_ANALYZED = auto()
    OCR_COMPLETED = auto()
    M5_SEMANTIC_RECONSTRUCTION = auto()
    COMPLETED = auto()
    FAILED = auto()
    PARTIAL_FAILURE = auto()
    M5_FAILURE = auto()
