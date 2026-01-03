"""
Adapters - Bridge components between MVVM and legacy GUI systems.

These adapters enable incremental migration from legacy controllers
to the MVVM pattern.
"""

from .dialogs_adapter import DialogsAdapter
from .examples_loader_adapter import ExamplesLoaderAdapter
from .execution_adapter import ExecutionAdapter
from .file_io_adapter import FileIOAdapter
from .layouts_adapter import LayoutsAdapter
from .palette_adapter import PaletteAdapter
from .theme_adapter import ThemeAdapter

try:
    from .plot_adapter import PlotAdapter
except ImportError:
    PlotAdapter = None

__all__ = [
    "DialogsAdapter",
    "ExecutionAdapter",
    "ExamplesLoaderAdapter",
    "FileIOAdapter",
    "LayoutsAdapter",
    "PaletteAdapter",
    "PlotAdapter",
    "ThemeAdapter",
]
