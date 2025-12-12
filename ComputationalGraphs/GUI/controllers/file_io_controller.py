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

    # === Phase 3: Save Selection and Import Graph ===

    def save_selection_as_graph(self):
        """Save selected nodes as a new graph file.

        Only saves nodes that are selected and edges between them.
        External edges (to nodes outside selection) are not included.
        """
        from ComputationalGraphs.GUI.node_item import NodeItem

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
            "Computational Graph (*.cgjson *.cgz);;Draw.io XML (*.drawio *.xml);;All Files (*)",
        )

        if not filename:
            return

        try:
            self.status_bar.showMessage(f"Importing {filename}...")

            # Load the graph
            if filename.lower().endswith((".drawio", ".xml")):
                imported_graph = DrawioIO.load(filename)
            else:
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
            imported_graph: The Graph object to merge
        """
        from ComputationalGraphs.GUI.node_item import NodeItem

        # Calculate offset: find bottom of existing nodes
        existing_bottom = 0
        for item in self.canvas.scene.items():
            if isinstance(item, NodeItem):
                bottom = item.pos().y() + item.radius * 2
                existing_bottom = max(existing_bottom, bottom)

        # Add padding below existing nodes
        offset_y = existing_bottom + 100 if existing_bottom > 0 else 0

        # Calculate centroid of imported nodes to center them
        imported_positions = []
        for node in imported_graph.nodes:
            x = getattr(node, "_visual_x", 0) or 0
            y = getattr(node, "_visual_y", 0) or 0
            imported_positions.append((x, y))

        if imported_positions:
            center_x = sum(p[0] for p in imported_positions) / len(imported_positions)
            center_y = sum(p[1] for p in imported_positions) / len(imported_positions)
        else:
            center_x, center_y = 0, 0

        # Get canvas center for horizontal positioning
        canvas_center_x = self.canvas.viewport().width() / 2

        # Map old nodes to new nodes for edge reconstruction
        old_to_new = {}

        # Import each node
        for i, node in enumerate(imported_graph.nodes):
            # Generate unique name
            original_name = getattr(node, "name", f"Imported_{i}")
            unique_name = self.canvas._generate_unique_name(original_name)

            # Get node class and create new instance
            node_class = type(node)
            try:
                new_node = node_class(unique_name)
            except TypeError:
                # Some nodes require additional constructor args
                try:
                    new_node = node_class(name=unique_name)
                except Exception:
                    # Last resort: create with just name
                    from ComputationalGraphs.Nodes.ContainerNode import ContainerNode

                    new_node = ContainerNode(unique_name)

            # Copy attributes
            for attr in ["value", "data", "size", "batchSize"]:
                if hasattr(node, attr):
                    try:
                        setattr(new_node, attr, getattr(node, attr))
                    except Exception:
                        pass

            # Add to current graph
            self.graph.AddNode(new_node)

            # Calculate position with offset
            old_x = getattr(node, "_visual_x", 0) or imported_positions[i][0]
            old_y = getattr(node, "_visual_y", 0) or imported_positions[i][1]

            # Shift to canvas center and below existing nodes
            new_x = old_x - center_x + canvas_center_x
            new_y = old_y - center_y + offset_y + 100

            # Create visual node item
            node_item = self.canvas.add_node_item(new_node, new_x, new_y)

            # Copy color if available
            old_color = getattr(node, "_visual_color", None)
            if old_color and node_item:
                try:
                    from PyQt6.QtGui import QColor

                    node_item.color = QColor(old_color)
                    node_item.update()
                except Exception:
                    pass

            old_to_new[node] = new_node

        # Reconstruct edges (only internal to imported graph)
        for old_node in imported_graph.nodes:
            new_node = old_to_new.get(old_node)
            if not new_node:
                continue

            for pred in getattr(old_node, "predecessors", []):
                new_pred = old_to_new.get(pred)
                if new_pred:
                    # Connect in graph
                    new_node.AddPreNode(new_pred)

                    # Create visual edge
                    source_item = self.canvas.node_items.get(new_pred)
                    target_item = self.canvas.node_items.get(new_node)
                    if source_item and target_item:
                        self.canvas.add_edge(source_item, target_item)

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
