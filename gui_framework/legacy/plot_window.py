"""Plot window module - compatibility layer using MVVM.

Plotting has been migrated to the MVVM system. This module provides
compatibility wrappers for legacy code that expects the old API.
"""

from typing import Any, List, Optional


def create_plot_window(nodes, max_iterations, parent=None, backend="auto"):
    """Create a plot window using the MVVM PlotAdapter.

    Args:
        nodes: List of node objects with .name and .value attributes
        max_iterations: Maximum iterations for the plot
        parent: Parent Qt widget
        backend: 'matplotlib', 'pyqtgraph', or 'auto'

    Returns:
        PlotWindow compatibility wrapper
    """
    # Determine backend
    if backend == "auto":
        try:
            import pyqtgraph

            backend = "pyqtgraph"
        except ImportError:
            backend = "matplotlib"

    return PlotWindow(nodes, max_iterations, parent=parent, backend=backend)


class PlotConfigDialog:
    """Deprecated stub; use PlotAdapter.show_config_dialog() instead."""

    def __init__(self, *args: Any, **kwargs: Any):
        raise RuntimeError(
            "Legacy PlotConfigDialog removed; use main_window.plot_adapter.show_config_dialog()"
        )


# Compatibility wrapper: provide a legacy-style PlotWindow that uses the MVVM PlotAdapter
class PlotWindow:
    """Compatibility PlotWindow implemented on top of PlotAdapter.

    Accepts legacy-style node objects with a `.name` and `.value` attribute and
    exposes a similar `update_plot(iteration)` method used by old tests and code.
    """

    def __init__(self, nodes, max_iterations, parent=None, backend="matplotlib"):
        from gui_framework.adapters.plot_adapter import PlotAdapter

        self._nodes = list(nodes) if nodes else []
        self._adapter = PlotAdapter(parent=parent)
        self._adapter.set_backend(backend)
        self.backend = backend
        self.max_iterations = max_iterations

        # Adapter expects node *names*/display labels — generate unique display labels for duplicates
        try:
            self._node_display_map = {}
            name_counts = {}
            node_display_names = []
            for n in self._nodes:
                base = getattr(n, "name", str(n))
                cnt = name_counts.get(base, 0)
                label = base if cnt == 0 else f"{base} ({cnt})"
                name_counts[base] = cnt + 1
                node_display_names.append(label)
                self._node_display_map[n] = label

            self._adapter._create_plot_window(node_display_names)
            if self._adapter.plot_viewmodel is not None:
                try:
                    self._adapter.plot_viewmodel.set_buffer_size(max_iterations)
                except Exception:
                    pass
            self._view = self._adapter.plot_view
        except Exception:
            self._view = None

    @property
    def nodes(self):
        """Return list of nodes being plotted."""
        return self._nodes

    @property
    def node_names(self):
        """Return list of node names being plotted."""
        return [n.name for n in self._nodes]

    def update_plot(self, iteration, active_subgraph=None):
        """Update plot with current node values."""
        # Collect current node values and forward to adapter using unique display labels
        data = {
            self._node_display_map.get(n, getattr(n, "name", str(n))): getattr(
                n, "value", 0
            )
            for n in self._nodes
        }
        self._adapter.update_plots_batch(data, iteration)
        self._adapter.set_iteration(iteration)
        if active_subgraph is not None:
            self._adapter.set_active_subgraph(active_subgraph)

    def add_node(self, node):
        """Add a node to the plot (legacy API).

        This wrapper ensures duplicate node names receive unique display labels
        so the underlying MVVM plot can show them separately.
        """
        if node not in self._nodes:
            self._nodes.append(node)
            # Generate a unique display label for this node based on existing labels
            base = getattr(node, "name", str(node))
            existing_count = sum(
                1
                for v in getattr(self, "_node_display_map", {}).values()
                if v == base or v.startswith(base + " (")
            )
            display_label = (
                base if existing_count == 0 else f"{base} ({existing_count})"
            )
            # Store mapping and notify adapter
            self._node_display_map[node] = display_label
            self._adapter.add_node(display_label)

    def show(self):
        """Show the plot window."""
        if self._view:
            self._view.show()

    def close(self):
        """Close the plot window."""
        try:
            self._adapter.close_plot_window()
        except Exception:
            pass

    def clear_plot(self):
        """Clear all plot data."""
        self._adapter.clear_plot()

    def isVisible(self):
        """Check if plot window is visible."""
        return self._adapter.is_plot_window_open()

    def grab(self):
        """Return a QPixmap of the underlying view for screenshotting."""
        if self._view:
            try:
                return self._view.grab()
            except Exception:
                pass
        raise AttributeError("Underlying view is not available to grab")

    def __getattr__(self, name):
        # Delegate attribute access to underlying view when possible
        if self._view and hasattr(self._view, name):
            return getattr(self._view, name)
        raise AttributeError(f"PlotWindow has no attribute {name}")
