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
        """Open the plot configuration dialog and create plot window."""
        from ComputationalGraphs.GUI.plot_window import (
            PlotConfigDialog,
            create_plot_window,
        )

        if not self.graph or len(self.graph.nodes) == 0:
            QMessageBox.warning(
                self.main_window, "No Graph", "Please load or create a graph first."
            )
            return

        # Get max iterations from the control panel
        default_max_iter = self.main_window.max_steps_spin.value()

        # Open configuration dialog
        config_dialog = PlotConfigDialog(self.graph, default_max_iter, self.main_window)
        if config_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_nodes = config_dialog.get_selected_nodes()

            if not selected_nodes:
                QMessageBox.warning(
                    self.main_window,
                    "No Nodes Selected",
                    "Please select at least one node to plot.",
                )
                return

            max_iterations = config_dialog.get_max_iterations()

            # Close existing plot window if backend mismatch
            if self.plot_window:
                selected_backend = self._get_selected_backend()
                try:
                    existing_backend = getattr(
                        self.plot_window, "backend", "matplotlib"
                    )
                except Exception:
                    existing_backend = "matplotlib"
                if existing_backend != selected_backend:
                    self.plot_window.close()
                    self.plot_window = None

            # Create new plot window (respecting backend choice)
            backend = self._get_selected_backend()
            self.plot_window = create_plot_window(
                selected_nodes, max_iterations, None, backend=backend
            )

            # Show backend name in the title
            display_backend = self._get_display_backend_name(backend)
            self.plot_window.setWindowTitle(
                f"Node Values Plot - Computational Graphs ({display_backend})"
            )
            self.plot_window.show()

            # Update plot with current iteration (if graph is running)
            if hasattr(self.main_window.graph_runner, "_iteration_counter"):
                self.plot_window.update_plot(
                    self.main_window.graph_runner._iteration_counter
                )

            self.status_bar.showMessage(f"Plotting {len(selected_nodes)} nodes")

    def add_selected_to_plot(self):
        """Add currently selected node(s) in the canvas to the plot window."""
        from ComputationalGraphs.GUI.node_item import NodeItem
        from ComputationalGraphs.GUI.plot_window import create_plot_window

        selected_items = self.canvas.scene.selectedItems()

        if not selected_items:
            QMessageBox.information(
                self.main_window,
                "No Selection",
                "Please select a node in the canvas first.",
            )
            return

        # Filter for node items only
        node_items = [item for item in selected_items if isinstance(item, NodeItem)]

        if not node_items:
            QMessageBox.information(
                self.main_window,
                "No Nodes Selected",
                "Please select a node (not an edge).",
            )
            return

        # Check backend consistency
        if self.plot_window:
            selected_backend = self._get_selected_backend()
            existing_backend = getattr(self.plot_window, "backend", "matplotlib")
            if existing_backend != selected_backend:
                # Recreate with selected backend
                self.plot_window.close()
                self.plot_window = None

        if not self.plot_window or not self.plot_window.isVisible():
            # Create with first selected node as standalone window
            max_iterations = self.main_window.max_steps_spin.value()
            first_node = node_items[0].node
            backend = self._get_selected_backend()
            self.plot_window = create_plot_window(
                [first_node], max_iterations, None, backend=backend
            )

            # Show backend name in the title
            display_backend = self._get_display_backend_name(backend)
            self.plot_window.setWindowTitle(
                f"Node Values Plot - Computational Graphs ({display_backend})"
            )
            self.plot_window.show()
            node_items = node_items[1:]  # Remove first node since it's already added

        # Add remaining selected nodes to plot
        for node_item in node_items:
            self.plot_window.add_node(node_item.node)

        node_count = len(
            [item for item in selected_items if isinstance(item, NodeItem)]
        )
        self.status_bar.showMessage(f"Added {node_count} node(s) to plot")

    def on_backend_changed(self, index):
        """Handle plot backend change; if a plot is open with a different backend, recreate it."""
        self.ensure_backend_consistency()

    def ensure_backend_consistency(self):
        """If a plot window exists with a different backend than selected, re-create it preserving plotted nodes."""
        from ComputationalGraphs.GUI.plot_window import create_plot_window

        if not hasattr(self.main_window, "plot_backend_combo"):
            return

        selected_backend = self._get_selected_backend()

        if self.plot_window is None:
            return

        existing_backend = getattr(self.plot_window, "backend", "matplotlib")
        if existing_backend == selected_backend:
            return

        # Preserve listed nodes
        try:
            current_nodes = list(self.plot_window.nodes)
            max_iterations = getattr(
                self.plot_window,
                "max_iterations",
                self.main_window.max_steps_spin.value(),
            )
        except Exception:
            current_nodes = []
            max_iterations = self.main_window.max_steps_spin.value()

        # Close and recreate
        try:
            self.plot_window.close()
        except Exception:
            pass

        self.plot_window = create_plot_window(
            current_nodes, max_iterations, None, backend=selected_backend
        )

        # Show backend name in the title
        display_backend = self._get_display_backend_name(selected_backend)
        self.plot_window.setWindowTitle(
            f"Node Values Plot - Computational Graphs ({display_backend})"
        )
        self.plot_window.show()
