"""
PlotAdapter: Bridge between new MVVM plot views and legacy GUI code.

Provides a familiar interface that the legacy MainWindow can use while
transparently using the new ViewModels and Views under the hood.
"""

from typing import List, Optional

try:
    from PyQt6.QtWidgets import QDialog

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


if PYQT_AVAILABLE:
    from ..viewmodels.plot_config_viewmodel import NodeInfo, PlotConfigViewModel
    from ..viewmodels.plot_viewmodel import PlotViewModel
    from ..views.plot_config_view import PlotConfigView
    from ..views.plot_view import PlotView


class PlotAdapter:
    """
    Adapter to use new MVVM plot system with legacy code.

    This adapter provides methods that mimic the old plot_window.py interface
    while using the new ViewModels and Views internally.

    Example:
        >>> # In MainWindow (legacy code)
        >>> from gui_framework.adapters.plot_adapter import PlotAdapter
        >>>
        >>> # Create adapter
        >>> self.plot_adapter = PlotAdapter(parent=self)
        >>>
        >>> # Show config dialog (old interface)
        >>> if self.plot_adapter.show_config_dialog(self.graph, max_iterations=1000):
        ...     # Config accepted, plot window is now open
        ...     pass
        >>>
        >>> # Update plot during execution (old interface)
        >>> self.plot_adapter.update_plot(node_name="A", value=3.14, iteration=5)
    """

    def __init__(self, parent=None):
        """
        Initialize PlotAdapter.

        Args:
            parent: Parent Qt widget
        """
        self.parent = parent
        self.plot_viewmodel: Optional[PlotViewModel] = None
        self.plot_view: Optional[PlotView] = None
        self.backend = "matplotlib"  # Default backend

    def show_config_dialog(self, graph, max_iterations: int = 100) -> bool:
        """
        Show plot configuration dialog (mimics old interface).

        Args:
            graph: Computational graph object
            max_iterations: Default max iterations

        Returns:
            True if user accepted dialog, False if cancelled
        """
        # Create config ViewModel
        config_vm = PlotConfigViewModel(max_iterations=max_iterations)

        # Convert graph nodes to NodeInfo objects
        nodes = []
        for node in graph.nodes:
            # Check if node is in a subgraph
            is_in_subgraph = False
            subgraph_name = None

            if hasattr(graph, "sub_graphs"):
                for sg in graph.sub_graphs:
                    if node in sg.nodes:
                        is_in_subgraph = True
                        subgraph_name = getattr(sg, "graph_name", "SubGraph")
                        break

            node_info = NodeInfo(
                name=node.name,
                node_id=str(id(node)),
                is_in_subgraph=is_in_subgraph,
                subgraph_name=subgraph_name,
            )
            nodes.append(node_info)

        config_vm.load_nodes(nodes)

        # Show dialog
        config_view = PlotConfigView(config_vm, parent=self.parent)

        if config_view.exec() == QDialog.DialogCode.Accepted:
            # User accepted - create plot window
            selected_nodes = config_vm.get_selected_nodes()
            max_iter = config_vm.get_max_iterations()

            if selected_nodes:
                self._create_plot_window(selected_nodes, max_iter)
                return True

        return False

    def _create_plot_window(self, node_names: List[str], max_iterations: int):
        """
        Create the plot window with selected nodes.

        Args:
            node_names: List of node names to plot
            max_iterations: Maximum iterations
        """
        # Create plot ViewModel
        self.plot_viewmodel = PlotViewModel(
            max_iterations=max_iterations, backend=self.backend
        )
        self.plot_viewmodel.set_nodes(node_names)

        # Create plot View
        self.plot_view = PlotView(self.plot_viewmodel, parent=self.parent)
        self.plot_view.show()

    def set_backend(self, backend: str):
        """
        Set plotting backend.

        Args:
            backend: 'matplotlib' or 'pyqtgraph'
        """
        self.backend = backend
        if self.plot_viewmodel:
            self.plot_viewmodel.set_backend(backend)

    def get_backend(self) -> str:
        """Get current backend."""
        return self.backend

    def is_plot_window_open(self) -> bool:
        """Check if plot window is currently open."""
        return self.plot_view is not None and self.plot_view.isVisible()

    def update_plot(
        self, node_name: str, value: float, iteration: Optional[int] = None
    ):
        """
        Update plot with new data point (mimics old interface).

        Args:
            node_name: Name of the node
            value: Value to plot
            iteration: Iteration number (optional)
        """
        if self.plot_viewmodel and node_name in self.plot_viewmodel.get_plotted_nodes():
            self.plot_viewmodel.add_data_point(node_name, value, iteration)

    def update_plots_batch(self, data: dict, iteration: Optional[int] = None):
        """
        Update multiple nodes at once.

        Args:
            data: Dictionary mapping node_name -> value
            iteration: Iteration number (optional)
        """
        if self.plot_viewmodel:
            self.plot_viewmodel.add_data_points(data, iteration)

    def set_iteration(self, iteration: int):
        """
        Set current iteration number.

        Args:
            iteration: Current iteration
        """
        if self.plot_viewmodel:
            self.plot_viewmodel.set_current_iteration(iteration)

    def clear_plot(self):
        """Clear all plot data."""
        if self.plot_viewmodel:
            self.plot_viewmodel.clear_data()

    def close_plot_window(self):
        """Close the plot window."""
        if self.plot_view:
            self.plot_view.close()
            self.plot_view = None
            self.plot_viewmodel = None

    def add_node(self, node_name: str):
        """
        Add a node to existing plot (mimics old interface).

        Args:
            node_name: Name of node to add
        """
        if self.plot_viewmodel:
            self.plot_viewmodel.add_node(node_name)

    def remove_node(self, node_name: str):
        """
        Remove a node from plot (mimics old interface).

        Args:
            node_name: Name of node to remove
        """
        if self.plot_viewmodel:
            self.plot_viewmodel.remove_node(node_name)

    def get_plotted_nodes(self) -> List[str]:
        """
        Get list of nodes being plotted.

        Returns:
            List of node names
        """
        if self.plot_viewmodel:
            return self.plot_viewmodel.get_plotted_nodes()
        return []


# Backwards compatibility alias
PlottingAdapter = PlotAdapter


# Stub for when PyQt not available
if not PYQT_AVAILABLE:

    class PlotAdapter:
        def __init__(self, parent=None):
            self.parent = parent

        def show_config_dialog(self, graph, max_iterations=100):
            return False

        def is_plot_window_open(self):
            return False

        def update_plot(self, node_name, value, iteration=None):
            pass

        def close_plot_window(self):
            pass
