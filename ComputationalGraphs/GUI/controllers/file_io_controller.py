"""
File I/O Controller - handles file operations.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages save/load/export operations for graphs.
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox

import ComputationalGraphs.Core.CGJsonIO as CGJsonIO
from ComputationalGraphs.Core.DrawioIO import DrawioIO
from ComputationalGraphs.Core.Graph import Graph


class FileIOController:
    """Controller for file I/O operations.

    Manages loading and saving of graph files in various formats
    (Draw.io XML, CGJson, etc.).
    """

    def __init__(self, main_window):
        """Initialize the file I/O controller.

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

    def new_graph(self):
        """Create a new empty graph."""
        reply = QMessageBox.question(
            self.main_window,
            "New Graph",
            "Are you sure? Current graph will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()

            # Replace graph via helper to sync canvas and graph_runner
            self.main_window.set_graph(Graph())
            self.main_window.graph_runner.reset()

            self.status_bar.showMessage("New graph created")

    def open_graph(self):
        """Open a graph from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Graph",
            "",
            "Computational Graph (.cgjson *.cgz);;Draw.io XML (*.drawio *.xml);;Python Files (*.py);;All Files (*)",
        )

        if filename:
            try:
                self.status_bar.showMessage(f"Opening {filename}...")

                if filename.lower().endswith((".drawio", ".xml")):
                    self._load_drawio(filename)
                elif filename.lower().endswith((".cgjson", ".cgz", ".json")):
                    self._load_cgjson(filename)
                else:
                    QMessageBox.information(
                        self.main_window,
                        "Not Implemented",
                        "Opening Python-constructed graph files (*.py) is not supported yet.\n"
                        "Use Draw.io XML format (*.drawio, *.xml) for saving/loading the GUI.",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Open Error",
                    f"Failed to open file {filename}: {e}",
                )

    def save_graph(self):
        """Save the current graph to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Graph",
            "",
            "Computational Graph (.cgjson *.cgz);;Draw.io XML (*.drawio *.xml);;Python Files (*.py);;All Files (*)",
        )

        if filename:
            try:
                # Ensure graph object is up-to-date from canvas
                try:
                    self.main_window.rebuild_graph()
                except Exception:
                    pass

                self.status_bar.showMessage(f"Saving to {filename}...")

                if filename.lower().endswith((".drawio", ".xml")):
                    # When saving from GUI, prefer to preserve canvas visuals (positions and colors)
                    DrawioIO.save(
                        self.graph,
                        filename,
                        canvas=self.canvas,
                        preserve_visuals=True,
                    )
                elif filename.lower().endswith((".cgjson", ".json", ".cgz")):
                    CGJsonIO.save(
                        self.graph,
                        filename,
                        canvas=self.canvas,
                        compress=filename.lower().endswith(".cgz"),
                    )
                else:
                    # Fallback to DrawioIO
                    DrawioIO.save(self.graph, filename + ".xml")

                self.status_bar.showMessage(f"Saved {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Save Error",
                    f"Failed to save file {filename}: {e}",
                )

    def _load_drawio(self, filename):
        """Load a Draw.io format graph."""
        graph = DrawioIO.load(filename)
        self._apply_loaded_graph(graph, filename)

    def _load_cgjson(self, filename):
        """Load a CGJson format graph."""
        graph = CGJsonIO.load(filename)
        self._apply_loaded_graph(graph, filename)

    def _apply_loaded_graph(self, graph, filename):
        """Apply a loaded graph to the canvas."""
        # Clear current canvas
        self.canvas.scene.clear()
        self.canvas.node_items.clear()
        self.canvas.edge_items.clear()

        # Set and visualize graph
        self.main_window.set_graph(graph)
        self.main_window._visualize_graph_on_canvas(graph)
        self.main_window.update_starting_nodes_display()
        self.main_window.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Loaded {filename}")
