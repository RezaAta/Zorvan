"""PyQtGraph-based plotting - compatibility wrapper using MVVM.

The original PyQtGraph implementation has been migrated to the MVVM system.
This module provides a thin wrapper for backward compatibility.

For new code, use:
- gui_framework.views.plot_view.PlotView for the MVVM view
- gui_framework.adapters.plot_adapter.PlotAdapter for the adapter
- zorvan.GUI.plot_window.PlotWindow for legacy compatibility
"""

from .plot_window import PlotWindow


class PlotWindowPG(PlotWindow):
    """Compatibility wrapper for legacy PlotWindowPG.

    This class now delegates to the MVVM PlotView via PlotWindow.
    It forces the pyqtgraph backend.
    """

    def __init__(self, nodes, max_iterations, parent=None):
        """Initialize PlotWindowPG with pyqtgraph backend.

        Args:
            nodes: List of node objects with .name and .value attributes
            max_iterations: Maximum iterations for the plot
            parent: Parent Qt widget
        """
        super().__init__(nodes, max_iterations, parent=parent, backend="pyqtgraph")
