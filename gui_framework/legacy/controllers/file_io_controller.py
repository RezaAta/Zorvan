"""
File I/O Controller - handles file operations.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages save/load/export operations for graphs.
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox

import zorvan.Core.CGJsonIO as CGJsonIO
from zorvan.Core.DrawioIO import DrawioIO
from zorvan.Core.Graph import Graph


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

    @graph.setter
    def graph(self, g):
        """Set the current graph on the main window using set_graph helper."""
        try:
            self.main_window.set_graph(g)
        except Exception:
            # Fallback to direct assignment if helper not available
            try:
                self.main_window.graph = g
            except Exception:
                pass

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    def _show_drawio_deprecated_warning(self):
        QMessageBox.information(
            self.main_window,
            "Deprecated Format",
            "Draw.io import/export is deprecated and will be removed in a future release. "
            "Use Computational Graph (.cgjson/.cgz) instead.",
        )

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

            # Trigger "Reset All" to ensure clean state for new graph
            try:
                self.main_window.reset_graph()
            except Exception:
                pass

            self.status_bar.showMessage("New graph created")

            # Notify MVVM adapter
            self._notify_mvvm_new_graph()

    def open_graph(self):
        """Open a graph from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Graph",
            "",
            "Computational Graph (.cgjson *.cgz);;Python Files (*.py);;All Files (*)",
        )

        if filename:
            try:
                self.status_bar.showMessage(f"Opening {filename}...")

                if filename.lower().endswith((".cgjson", ".cgz", ".json")):
                    self._load_cgjson(filename)
                elif filename.lower().endswith((".drawio", ".xml")):
                    QMessageBox.information(
                        self.main_window,
                        "Unsupported Format",
                        "Draw.io import is no longer supported. Use Computational Graph (.cgjson/.cgz) files instead.",
                    )
                else:
                    QMessageBox.information(
                        self.main_window,
                        "Not Implemented",
                        "Opening Python-constructed graph files (*.py) is not supported yet.\n"
                        "Use Computational Graph (.cgjson/.cgz) for saving/loading the GUI.",
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
            "Computational Graph (.cgjson *.cgz);;Draw.io XML (*.drawio *.xml) [deprecated];;Python Files (*.py);;All Files (*)",
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
                    self._show_drawio_deprecated_warning()
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

                # Notify MVVM adapter
                self._notify_mvvm_file_saved(filename)
            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Save Error",
                    f"Failed to save file {filename}: {e}",
                )

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
        # Clear subgraph control widgets
        try:
            self.canvas._subgraph_widgets.clear()
        except Exception:
            pass

        # Set and visualize graph
        self.main_window.set_graph(graph)
        self.main_window._visualize_graph_on_canvas(graph)
        self.main_window.update_starting_nodes_display()
        self.main_window.update_stopping_nodes_display()

        # Ensure execution controls and processor are reset when a new file is loaded
        # (mirrors behavior of New -> keeps UI predictable and stops any running processor)
        try:
            self.main_window.reset_graph()
        except Exception:
            pass

        # Process any pending Qt events to flush stale step_completed signals
        try:
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()
        except Exception:
            pass

        # Explicitly ensure step counter displays 0 (guard against stale queued signals)
        try:
            max_steps = self.main_window.max_steps_spin.value()
            self.main_window.step_label.setText(f"Step: 0 / {max_steps}")
            if (
                hasattr(self.main_window, "step_progress")
                and self.main_window.step_progress
            ):
                self.main_window.step_progress.setValue(0)
                self.main_window.step_progress.setMaximum(max_steps)
        except Exception:
            pass

        # Force UI refresh so step counter displays immediately
        try:
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()
        except Exception:
            pass

        # Update graph selector for multi-graph support
        try:
            self.main_window.update_graph_selector()
        except Exception:
            pass

        # Update subgraph control widgets (labels and buttons)
        try:
            self.canvas.update_subgraph_controls()
        except Exception:
            pass

        self.status_bar.showMessage(f"Loaded {filename}")

        # Notify MVVM adapter
        self._notify_mvvm_file_opened(filename)

    # === Phase 3: Save Selection and Import Graph ===

    def save_selection_as_graph(self):
        """Save selected nodes as a new graph file.

        Only saves nodes that are selected and edges between them.
        External edges (to nodes outside selection) are not included.
        """
        from gui_framework.legacy.node_item import NodeItem

        # Get selected node items
        selected_items = [
            item
            for item in self.canvas.scene.selectedItems()
            if isinstance(item, NodeItem)
        ]

        if not selected_items:
            QMessageBox.warning(
                self.main_window,
                "No Selection",
                "Please select nodes to save.",
            )
            return

        # Get file path
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Selection As",
            "",
            "Computational Graph (*.cgjson *.cgz);;All Files (*)",
        )

        if not filename:
            return

        try:
            # Create a temporary graph from selected nodes
            temp_graph = Graph(name="Exported Selection")
            selected_nodes = [item.node for item in selected_items]
            selected_set = set(selected_nodes)

            # Add nodes to temp graph
            for node in selected_nodes:
                temp_graph.nodes.append(node)
                temp_graph.idToNodeDictionary[node.id] = node

            # Build adjacency matrix (only for internal edges)
            temp_graph.UpdateAdjacencyMatrix()

            # Save with visuals - create a mini canvas dict for positions
            # We need to pass the real canvas so CGJsonIO can get positions
            CGJsonIO.save(
                temp_graph,
                filename,
                canvas=self.canvas,
                compress=filename.lower().endswith(".cgz"),
            )

            self.status_bar.showMessage(
                f"Saved {len(selected_nodes)} nodes to {filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Save Error",
                f"Failed to save selection: {e}",
            )

    def import_graph_to_canvas(self):
        """Import a graph file and merge it into the current canvas.

        - Loads the graph from file
        - Auto-renames nodes to avoid conflicts
        - Positions imported nodes below existing content
        - Registers imported graph as a sub-graph
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Import Graph",
            "",
            "Computational Graph (*.cgjson *.cgz);;All Files (*)",
        )

        if not filename:
            return

        try:
            self.status_bar.showMessage(f"Importing {filename}...")

            # Load the graph
            if filename.lower().endswith((".drawio", ".xml")):
                QMessageBox.information(
                    self.main_window,
                    "Unsupported Format",
                    "Draw.io import is no longer supported. Use Computational Graph (.cgjson/.cgz) files instead.",
                )
                return
            imported_graph = CGJsonIO.load(filename)

            if not imported_graph or not imported_graph.nodes:
                QMessageBox.warning(
                    self.main_window,
                    "Empty Graph",
                    "The imported graph is empty.",
                )
                return

            self._merge_graph_into_canvas(imported_graph)

            self.status_bar.showMessage(
                f"Imported {len(imported_graph.nodes)} nodes from {filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Import Error",
                f"Failed to import graph: {e}",
            )

    def _merge_graph_into_canvas(self, imported_graph):
        """Merge an imported graph into the current canvas.

        Args:
            imported_graph: The Graph object to merge (already has nodes connected)
        """
        from gui_framework.legacy.node_item import NodeItem

        # Calculate offset: find bottom of existing nodes
        existing_bottom = 0
        for item in self.canvas.scene.items():
            if isinstance(item, NodeItem):
                bottom = item.pos().y() + item.radius * 2
                existing_bottom = max(existing_bottom, bottom)

        # Add padding below existing nodes
        offset_y = existing_bottom + 100 if existing_bottom > 0 else 0

        # Collect positions from imported nodes (using gui_pos attribute set by CGJsonIO.load)
        imported_positions = []
        for node in imported_graph.nodes:
            pos = getattr(node, "gui_pos", None)
            if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                imported_positions.append((float(pos[0]), float(pos[1])))
            else:
                imported_positions.append((0.0, 0.0))

        # Calculate centroid of imported nodes
        if imported_positions:
            center_x = sum(p[0] for p in imported_positions) / len(imported_positions)
            center_y = sum(p[1] for p in imported_positions) / len(imported_positions)
        else:
            center_x, center_y = 0, 0

        # Get canvas center for horizontal positioning
        canvas_center_x = self.canvas.viewport().width() / 2

        # Get existing node names for conflict detection
        existing_names = {n.name for n in self.graph.nodes}

        # Map old nodes to new nodes (for name conflict handling)
        old_to_new = {}

        # Import each node - use the actual loaded node (preserves connections)
        for i, node in enumerate(imported_graph.nodes):
            original_name = getattr(node, "name", f"Imported_{i}")

            # Check for name conflicts and rename if needed
            if original_name in existing_names:
                unique_name = self._generate_unique_name(original_name, existing_names)
                node.name = unique_name

            existing_names.add(node.name)

            # Add to current graph (the node already has its connections from CGJsonIO.load)
            self.graph.AddNode(node)

            # Calculate position with offset (preserve relative layout)
            old_x, old_y = imported_positions[i]

            # Shift: center horizontally, offset vertically below existing nodes
            new_x = old_x - center_x + canvas_center_x
            new_y = old_y - center_y + offset_y + 100

            # Create visual node item at the computed position
            node_item = self.canvas.add_node_item(node, new_x, new_y)

            # Copy color if available (from gui_color attribute)
            old_color = getattr(node, "gui_color", None)
            if old_color and node_item:
                try:
                    from PyQt6.QtGui import QColor

                    node_item.color = QColor(old_color)
                    node_item.update()
                except Exception:
                    pass

            old_to_new[node] = node

        # Create visual edges for all connections in imported graph
        # The nodes already have predecessors set by CGJsonIO.load, we just need visual edges
        for node in imported_graph.nodes:
            # Ensure this node has a visual item
            target_item = self.canvas.node_items.get(node)
            if not target_item:
                continue

            for pred in getattr(node, "predecessors", []):
                # Only create edge if predecessor is also in imported graph
                if pred in old_to_new:
                    # Call add_edge_item with node objects (not NodeItem objects)
                    try:
                        self.canvas.add_edge_item(pred, node)
                    except Exception:
                        # Fallback to adding by using NodeItem objects if needed
                        source_item = self.canvas.node_items.get(pred)
                        if source_item and target_item:
                            self.canvas.add_edge_item(source_item, target_item)

        # Update adjacency matrix
        self.graph.UpdateAdjacencyMatrix()

        # Create a sub-graph from the imported nodes
        imported_name = getattr(imported_graph, "graph_name", "Imported Graph")
        try:
            new_nodes = list(old_to_new.values())
            subgraph = self.graph.create_subgraph_from_nodes(new_nodes, imported_name)
            if subgraph:
                self.canvas.refresh_subgraph_visuals()
                self.main_window.update_graph_selector()
        except Exception:
            # If subgraph creation fails, nodes are still imported
            pass

    def _generate_unique_name(self, base_name, existing_names):
        """Generate a unique name by appending _N suffix."""
        if base_name not in existing_names:
            return base_name
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        return f"{base_name}_{counter}"

    # === MVVM Integration Methods ===

    def _notify_mvvm_file_opened(self, file_path: str):
        """Notify MVVM adapter that a file was opened."""
        try:
            if (
                hasattr(self.main_window, "file_io_adapter")
                and self.main_window.file_io_adapter
            ):
                self.main_window.file_io_adapter.notify_file_opened(file_path)
        except Exception:
            pass

    def _notify_mvvm_file_saved(self, file_path: str):
        """Notify MVVM adapter that a file was saved."""
        try:
            if (
                hasattr(self.main_window, "file_io_adapter")
                and self.main_window.file_io_adapter
            ):
                self.main_window.file_io_adapter.notify_file_saved(file_path)
        except Exception:
            pass

    def _notify_mvvm_new_graph(self):
        """Notify MVVM adapter that a new graph was created."""
        try:
            if (
                hasattr(self.main_window, "file_io_adapter")
                and self.main_window.file_io_adapter
            ):
                self.main_window.file_io_adapter.notify_new_graph()
        except Exception:
            pass
