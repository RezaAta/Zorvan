"""Examples loader compatibility layer for gui_framework."""

from .legacy import ExamplesLoader

if ExamplesLoader is None:
    raise ImportError("Legacy examples loader not available")

__all__ = ["ExamplesLoader"]
