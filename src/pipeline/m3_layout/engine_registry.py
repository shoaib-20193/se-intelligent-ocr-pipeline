from dataclasses import dataclass

@dataclass
class BackendCapabilities:
    polygons: bool
    rotated_boxes: bool
    word_level: bool
    confidence_scores: bool

def get_backend_capabilities(backend_name: str) -> BackendCapabilities:
    """Returns the capabilities of the specified layout backend."""
    name = backend_name.lower()
    if name == "doctr":
        return BackendCapabilities(
            polygons=True,
            rotated_boxes=False,
            word_level=True,
            confidence_scores=True
        )
    elif name == "classical_cv":
        return BackendCapabilities(
            polygons=False,
            rotated_boxes=False,
            word_level=False,
            confidence_scores=False
        )
    raise ValueError(f"Unknown layout backend: {backend_name}")
