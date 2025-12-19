"""
Graph Builder Controller - handles building and visualizing graphs on the canvas.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages the instantiation and visualization of graph nodes and edges.
"""

import time

from PyQt6.QtWidgets import QApplication, QMessageBox


class GraphBuilderController:
    """Controller for building and visualizing graphs on the canvas.

    Manages the creation of NodeItems and EdgeItems from a Graph object,
    layout computation, collision avoidance, and visual updates.
    """

    def __init__(self, main_window):
        """Initialize the graph builder controller.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def graph(self):
        """Access the graph from main window."""
        return self.main_window.graph

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    def _is_verbose(self):
        """Check if verbose mode is enabled."""
        try:
            return (
                hasattr(self.main_window, "verbose_check")
                and self.main_window.verbose_check.isChecked()
            )
        except Exception:
            return False

    def visualize_graph_on_canvas(self, graph):
        """Visualize a graph object on the canvas.

        Args:
            graph: The Graph object to visualize
        """
        try:
            # Import node_item here to avoid circular import
            import networkx as nx

            from ComputationalGraphs.GUI.edge_item import EdgeItem
            from ComputationalGraphs.GUI.node_item import NodeItem

            # Clear existing canvas items first
            self.canvas.scene.clear()
            self.canvas.node_items.clear()
            self.canvas.edge_items.clear()

            # Create a networkx graph for layout
            G = nx.DiGraph()

            # Add nodes to networkx graph
            for node in graph.nodes:
                G.add_node(node)

            # Add edges based on predecessors
            for node in graph.nodes:
                if hasattr(node, "predecessors") and node.predecessors:
                    for pred in node.predecessors:
                        G.add_edge(pred, node)

            # Compute layout
            t0 = time.time()
            num_nodes = len(G.nodes())
            base_scale = 300
            scale = base_scale * max(1.0, num_nodes / 15)

            # Check for explicit GUI positions from file
            pos, use_gui_positions = self._get_layout_positions(graph, G, scale)

            t1 = time.time()
            import logging

            logger = logging.getLogger(__name__)
            if self._is_verbose():
                logger.debug(
                    "Layout computed in %.3fs for %d nodes (ANN algorithm)",
                    (t1 - t0),
                    num_nodes,
                )

            # Create node items
            t2 = self._create_node_items(graph, pos, use_gui_positions, NodeItem)

            # Create edge items
            t3 = self._create_edge_items(graph, EdgeItem)

            # Update visuals
            t4 = time.time()
            try:
                if self.main_window.colorize_enabled:
                    self.main_window.auto_detect_range()
                else:
                    self.canvas.update_node_visuals(False, 0, 1)
            except Exception as exc:
                import logging

                logging.getLogger(__name__).exception(
                    "Error while updating node visuals: %s", exc
                )
                raise

            t5 = time.time()
            if self._is_verbose():
                print(
                    f"Node creation {t2 - t1:.3f}s, Edge creation {t3 - t2:.3f}s, Visual update {t5 - t4:.3f}s"
                )

        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                "Visualization Error",
                f"Graph loaded but visualization failed:\n{str(e)}\n\n"
                "You can still run the graph, but the visual layout may not be optimal.",
            )

    def _get_layout_positions(self, graph, G, scale):
        """Get layout positions for nodes.

        Returns:
            tuple: (positions dict, use_gui_positions bool)
        """
        import networkx as nx

        # If all nodes have explicit GUI positions (loaded from file), use them
        gui_positions = {node: getattr(node, "gui_pos", None) for node in graph.nodes}
        use_gui_positions = all(gui_positions.values())

        if use_gui_positions:
            pos = {node: tuple(gui_positions[node]) for node in graph.nodes}
        else:
            # Compute automatic layout
            try:
                pos = self.canvas.apply_layout("ann")
            except Exception as e:
                # Fallback to networkx spring layout
                num_nodes = len(G.nodes())
                try:
                    print(
                        f"[GUI] ANN layout not available ({e}); falling back to spring layout for {num_nodes} nodes"
                    )
                    pos = nx.spring_layout(
                        G, k=2.0 / num_nodes**0.5, iterations=50, scale=scale, seed=42
                    )
                except Exception:
                    # Final fallback: circular layout
                    pos = nx.circular_layout(G, scale=scale)

        return pos, use_gui_positions

    def _create_node_items(self, graph, pos, use_gui_positions, NodeItem):
        """Create NodeItem objects for all nodes.

        Returns:
            float: Time after node creation
        """
        # Disable snap to grid if using GUI positions
        old_snap, old_snap_while = None, None
        if use_gui_positions:
            try:
                old_snap = getattr(self.canvas, "snap_to_grid", False)
                old_snap_while = getattr(self.canvas, "snap_while_dragging", False)
                self.canvas.set_snap_to_grid(False)
                self.canvas.set_snap_while_dragging(False)
            except Exception:
                pass

        min_distance = 100
        created_positions = {}

        for node_idx, node in enumerate(graph.nodes):
            # Process events periodically to keep UI responsive
            if node_idx % 50 == 0:
                try:
                    QApplication.processEvents()
                except Exception:
                    pass

            node_pos = pos.get(node, (0, 0))
            x, y = node_pos[0], node_pos[1]

            # Determine if collision adjustment should be skipped
            skip_collision = self._should_skip_collision(node, use_gui_positions)

            # Adjust position to avoid collisions
            adjusted_x, adjusted_y = self._adjust_for_collisions(
                x, y, created_positions, min_distance, skip_collision
            )

            # Store position and create node
            created_positions[node] = (adjusted_x, adjusted_y)

            try:
                node_item = NodeItem(node, adjusted_x, adjusted_y)
                try:
                    node_item.canvas = self.canvas
                except Exception:
                    pass
                self.canvas.scene.addItem(node_item)
                self.canvas.node_items[node] = node_item

                # Reapply exact position if using GUI positions
                if use_gui_positions:
                    try:
                        node_item.setPos(adjusted_x, adjusted_y)
                    except Exception:
                        pass
                # Apply saved GUI visuals if provided by the node (color, radius, label)
                try:
                    gui_col = getattr(node, "gui_color", None)
                    if gui_col:
                        from PyQt6.QtGui import QColor

                        # Drawio style color is usually hex like #RRGGBB
                        try:
                            qcol = QColor(gui_col)
                            node_item.manual_color = qcol
                            node_item.color = qcol
                            node_item.update()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    gui_radius = getattr(node, "gui_radius", None)
                    if gui_radius:
                        node_item.radius = gui_radius
                        try:
                            node_item.setRect(
                                -gui_radius, -gui_radius, gui_radius * 2, gui_radius * 2
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    gui_label = getattr(node, "gui_label", None)
                    if gui_label:
                        node_item.set_label_text(gui_label)
                except Exception:
                    pass
                try:
                    gui_label_color = getattr(node, "gui_label_color", None)
                    if gui_label_color:
                        from PyQt6.QtGui import QColor

                        try:
                            node_item.label.setDefaultTextColor(QColor(gui_label_color))
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                print(
                    f"Failed to create NodeItem for node: {getattr(node, 'name', str(node))}"
                )
                raise

        # Restore snap settings
        if use_gui_positions:
            try:
                if old_snap is not None:
                    self.canvas.set_snap_to_grid(old_snap)
                if old_snap_while is not None:
                    self.canvas.set_snap_while_dragging(old_snap_while)
            except Exception:
                pass

        return time.time()

    def _should_skip_collision(self, node, use_gui_positions):
        """Determine if collision adjustment should be skipped for a node."""
        if use_gui_positions:
            return True

        nm = getattr(node, "name", "")

        # Check if node is a ContainerNode
        try:
            from ComputationalGraphs.Nodes.ContainerNode import ContainerNode

            is_container = isinstance(node, ContainerNode)
        except Exception:
            is_container = False

        # Check lock setting
        try:
            lock = getattr(self.main_window, "lock_diagonal_layout_check", None)
            lock_enabled = lock.isChecked() if lock is not None else True
        except Exception:
            lock_enabled = True

        return lock_enabled and (
            is_container or nm.startswith("dW_") or nm.startswith("dw_")
        )

    def _adjust_for_collisions(
        self, x, y, created_positions, min_distance, skip_collision
    ):
        """Adjust position to avoid collisions with existing nodes."""
        import random

        if skip_collision:
            return x, y

        adjusted_x, adjusted_y = x, y
        max_attempts = 50

        for attempt in range(max_attempts):
            collision = False
            for other_pos in created_positions.values():
                dx = adjusted_x - other_pos[0]
                dy = adjusted_y - other_pos[1]
                distance = (dx**2 + dy**2) ** 0.5

                if distance < min_distance:
                    collision = True
                    if distance > 0:
                        push_x = (dx / distance) * (min_distance - distance)
                        push_y = (dy / distance) * (min_distance - distance)
                        adjusted_x += push_x * 0.5
                        adjusted_y += push_y * 0.5
                    else:
                        # Exactly overlapping - add random offset
                        adjusted_x += random.uniform(-50, 50)
                        adjusted_y += random.uniform(-50, 50)

            if not collision:
                break

        return adjusted_x, adjusted_y

    def _create_edge_items(self, graph, EdgeItem):
        """Create EdgeItem objects for all edges.

        Returns:
            float: Time after edge creation
        """
        import time

        for edge_idx, node in enumerate(graph.nodes):
            if hasattr(node, "predecessors") and node.predecessors:
                target_item = self.canvas.node_items.get(node)
                if target_item:
                    for pred in node.predecessors:
                        source_item = self.canvas.node_items.get(pred)
                        if source_item:
                            try:
                                edge = EdgeItem(source_item, target_item)
                            except Exception:
                                print(
                                    f"Failed to create EdgeItem: {getattr(pred, 'name', pred)} -> {getattr(node, 'name', node)}"
                                )
                                raise
                            self.canvas.scene.addItem(edge)
                            self.canvas.edge_items.append(edge)
                            source_item.add_edge(edge)
                            target_item.add_edge(edge)

            # Process events periodically
            if edge_idx % 50 == 0:
                try:
                    QApplication.processEvents()
                except Exception:
                    pass

        return time.time()
