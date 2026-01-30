"""
Plotting Controller - handles plot window management.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages the plot window creation, node addition, and backend switching.
"""

from PyQt6.QtWidgets import QDialog, QMessageBox


class PlottingController:
    """Controller for plot window management.

    Manages opening plot windows, adding nodes to plots,
    and handling backend (PyQtGraph/Matplotlib) switching.
    """

    def __init__(self, main_window):
        """Initialize the plotting controller.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window

    @property
    def graph(self):
        """Access the current graph from main window."""
        return self.main_window.graph

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    @property
    def plot_window(self):
        """Access the plot window from main window."""
        return self.main_window.plot_window

    @plot_window.setter
    def plot_window(self, value):
        """Set the plot window on main window."""
        self.main_window.plot_window = value

    def _get_selected_backend(self):
        """Get the currently selected backend from the combo box."""
        if hasattr(self.main_window, "plot_backend_combo"):
            return (
                "pyqtgraph"
                if self.main_window.plot_backend_combo.currentText() == "PyQtGraph"
                else "matplotlib"
            )
        return "matplotlib"

    def _get_display_backend_name(self, backend):
        """Get display name for backend."""
        return "PyQtGraph" if backend == "pyqtgraph" else "Matplotlib"

    def open_plot_window(self):
        """Open the plot configuration dialog and create plot window.

        Uses MVVM PlotAdapter.
        """
        mw = self.main_window

        if not self.graph or len(self.graph.nodes) == 0:
            QMessageBox.warning(mw, "No Graph", "Please load or create a graph first.")
            return

        # Ensure plot_adapter exists
        if not hasattr(mw, "plot_adapter") or mw.plot_adapter is None:
            from gui_framework.adapters.plot_adapter import PlotAdapter

            mw.plot_adapter = PlotAdapter(parent=mw)

        # Get max iterations from the control panel
        default_max_iter = mw.max_steps_spin.value()

        # Set backend on adapter
        backend = self._get_selected_backend()
        mw.plot_adapter.set_backend(backend)

        # Show config dialog via MVVM
        result = mw.plot_adapter.show_config_dialog(
            self.graph, max_iterations=default_max_iter
        )

        if result:
            # Store reference for legacy compatibility
            if mw.plot_adapter.plot_view:
                self.plot_window = mw.plot_adapter.plot_view

                # Set window title with backend name
                display_backend = self._get_display_backend_name(backend)
                self.plot_window.setWindowTitle(
                    f"Node Values Plot - Computational Graphs ({display_backend})"
                )
            self.status_bar.showMessage("Plot window opened")

    def add_selected_to_plot(self):
        """Add currently selected node(s) in the canvas to the plot window."""
        from ComputationalGraphs.GUI.node_item import NodeItem

        mw = self.main_window
        selected_items = self.canvas.scene.selectedItems()

        if not selected_items:
            QMessageBox.information(
                mw,
                "No Selection",
                "Please select a node in the canvas first.",
            )
            return

        # Filter for node items only
        node_items = [item for item in selected_items if isinstance(item, NodeItem)]

        if not node_items:
            QMessageBox.information(
                mw,
                "No Nodes Selected",
                "Please select a node (not an edge).",
            )
            return

        # Ensure plot_adapter exists
        if not hasattr(mw, "plot_adapter") or mw.plot_adapter is None:
            from gui_framework.adapters.plot_adapter import PlotAdapter

            mw.plot_adapter = PlotAdapter(parent=mw)

        # Check backend consistency
        backend = self._get_selected_backend()
        mw.plot_adapter.set_backend(backend)

        if self.plot_window:
            existing_backend = getattr(self.plot_window, "backend", "matplotlib")
            if existing_backend != backend:
                # Close and recreate
                try:
                    self.plot_window.close()
                except Exception:
                    pass
                self.plot_window = None

        if not self.plot_window or not self.plot_window.isVisible():
            # Create plot window with first selected node
            node_names = [n.node.name for n in node_items]
            mw.plot_adapter._create_plot_window(node_names)
            self.plot_window = mw.plot_adapter.plot_view

            if self.plot_window:
                # Set window title with backend name
                display_backend = self._get_display_backend_name(backend)
                self.plot_window.setWindowTitle(
                    f"Node Values Plot - Computational Graphs ({display_backend})"
                )
                self.plot_window.show()
        else:
            # Add remaining selected nodes to existing plot
            for node_item in node_items:
                try:
                    mw.plot_adapter.add_node(node_item.node.name)
                except Exception:
                    pass

        node_count = len(node_items)
        self.status_bar.showMessage(f"Added {node_count} node(s) to plot")

    def on_backend_changed(self, index):
        """Handle plot backend change; if a plot is open with a different backend, recreate it."""
        self.ensure_backend_consistency()

    def ensure_backend_consistency(self):
        """If a plot window exists with a different backend than selected, re-create it preserving plotted nodes."""
        mw = self.main_window

        if not hasattr(mw, "plot_backend_combo"):
            return

        selected_backend = self._get_selected_backend()

        if self.plot_window is None:
            return

        existing_backend = getattr(self.plot_window, "backend", "matplotlib")
        if existing_backend == selected_backend:
            return

        # Preserve listed nodes (as names)
        try:
            current_node_names = list(
                getattr(self.plot_window, "node_names", [])
                or [n.name for n in getattr(self.plot_window, "nodes", [])]
            )
            max_iterations = getattr(
                self.plot_window,
                "max_iterations",
                mw.max_steps_spin.value(),
            )
        except Exception:
            current_node_names = []
            max_iterations = mw.max_steps_spin.value()

        # Close existing
        try:
            self.plot_window.close()
        except Exception:
            pass

        # Ensure plot_adapter exists
        if not hasattr(mw, "plot_adapter") or mw.plot_adapter is None:
            from gui_framework.adapters.plot_adapter import PlotAdapter

            mw.plot_adapter = PlotAdapter(parent=mw)

        # Recreate with new backend
        mw.plot_adapter.set_backend(selected_backend)
        if current_node_names:
            mw.plot_adapter._create_plot_window(current_node_names, max_iterations)
            self.plot_window = mw.plot_adapter.plot_view

            if self.plot_window:
                # Show backend name in the title
                display_backend = self._get_display_backend_name(selected_backend)
                self.plot_window.setWindowTitle(
                    f"Node Values Plot - Computational Graphs ({display_backend})"
                )
                self.plot_window.show()
