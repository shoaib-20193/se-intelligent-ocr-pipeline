"""
M3 Spatial Layout Intelligence Layer
Strictly spatial/geometric. Semantics forbidden.
"""
from .interface import M3LayoutEngine
from .engine_registry import BackendCapabilities, get_backend_capabilities

__all__ = ["M3LayoutEngine", "BackendCapabilities", "get_backend_capabilities"]
