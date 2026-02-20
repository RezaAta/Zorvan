"""
SimplifyCommand - Undoable commands for graph simplification operations.

Provides three commands:
- SimplifyStepCommand: Apply one simplification step
- FullySimplifyCommand: Apply all possible simplifications
- ExpandStepCommand: Reverse the last simplification
"""

from PyQt6.QtGui import QUndoCommand


def _get_main_window(canvas):
    """Get the main window from the canvas."""
    # Try parent() first (canvas is usually a child of main window)
    if hasattr(canvas, "parent") and callable(canvas.parent):
        parent = canvas.parent()
        if parent and hasattr(parent, "graph_builder_controller"):
            return parent
    # Try main_window attribute
    if hasattr(canvas, "main_window"):
        return canvas.main_window
    return None


class SimplifyStepCommand(QUndoCommand):
    """Command to apply one step of graph simplification.

    Stores the graph state before simplification to enable undo.
    """

    def __init__(self, canvas, graph, description="Simplify Step"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.result = None

        # Store state before simplification for undo
        self._store_graph_state()

    def _store_graph_state(self):
        """Store current graph state for undo."""
        # Store node data: (node, x, y, manual_color)
        self.original_nodes = []
        self.original_edges = []

        for node in self.graph.nodes:
            if node in self.canvas.node_items:
                node_item = self.canvas.node_items[node]
                pos = node_item.pos()
                manual_color = getattr(node_item, "manual_color", None)
                self.original_nodes.append((node, pos.x(), pos.y(), manual_color))

        # Store edges
        for node in self.graph.nodes:
            for pred in node.predecessors:
                edge_tuple = (pred, node)
                if edge_tuple not in self.original_edges:
                    self.original_edges.append(edge_tuple)

    def redo(self):
        """Apply simplification step."""
        self.result = self.graph.simplify_step()

        if self.result and self.result.get("changed"):
            self._refresh_canvas()

    def undo(self):
        """Undo simplification by expanding the last operation."""
        if self.result and self.result.get("changed"):
            # Use expand_step to reverse
            self.graph.expand_step()
            self._refresh_canvas()

    def _refresh_canvas(self):
        """Refresh the canvas to reflect graph changes."""
        mw = _get_main_window(self.canvas)
        if mw and hasattr(mw, "graph_builder_controller"):
            mw.graph_builder_controller.visualize_graph_on_canvas(self.graph)


class FullySimplifyCommand(QUndoCommand):
    """Command to fully simplify a graph.

    Stores the complete graph state before simplification to enable undo.
    """

    def __init__(self, canvas, graph, description="Fully Simplify"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.result = None

        # Store the number of operations for undo
        self.operations_count = 0

        # Store positions for nodes that will be recreated
        self.node_positions = {}
        for node in self.graph.nodes:
            if node in self.canvas.node_items:
                node_item = self.canvas.node_items[node]
                pos = node_item.pos()
                self.node_positions[node.name] = (pos.x(), pos.y())

    def redo(self):
        """Apply full simplification."""
        # Clear history before starting
        initial_history = self.graph.get_simplification_history_count()

        self.result = self.graph.simplify_fully()

        # Calculate how many operations were added
        final_history = self.graph.get_simplification_history_count()
        self.operations_count = final_history - initial_history

        self._refresh_canvas()

    def undo(self):
        """Undo full simplification by expanding all operations."""
        # Expand each operation in reverse order
        for _ in range(self.operations_count):
            self.graph.expand_step()

        self._refresh_canvas()

    def _refresh_canvas(self):
        """Refresh the canvas to reflect graph changes."""
        mw = _get_main_window(self.canvas)
        if mw and hasattr(mw, "graph_builder_controller"):
            mw.graph_builder_controller.visualize_graph_on_canvas(self.graph)


class ExpandStepCommand(QUndoCommand):
    """Command to expand (reverse) the last simplification.

    This is the inverse of SimplifyStepCommand.
    """

    def __init__(self, canvas, graph, description="Expand Step"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.result = None

        # Store the operation that will be expanded (for redo after undo)
        self.expanded_operation = None

    def redo(self):
        """Expand the last simplified node."""
        # Get the last operation before expanding (for potential re-simplification)
        has_history = hasattr(self.graph, "_simplification_history")
        if has_history and self.graph._simplification_history:
            self.expanded_operation = self.graph._simplification_history[-1]
        else:
            self.expanded_operation = None

        self.result = self.graph.expand_step()

        if self.result and self.result.get("expanded"):
            self._refresh_canvas()

    def undo(self):
        """Undo the expansion (re-apply the simplification)."""
        if self.expanded_operation:
            # Re-apply the operation that was expanded
            op_type = self.expanded_operation[0]

            if op_type == "compress":
                # Get the nodes that were restored and re-compress them
                nodes = self.result.get("nodes", [])
                if len(nodes) >= 2:
                    can_compress, _ = self.graph.can_compress_nodes(nodes)
                    if can_compress:
                        self.graph.CompressNodes(nodes)
                        self.graph._simplification_history.append(
                            self.expanded_operation
                        )
            elif op_type == "abstract":
                # Get the nodes that were restored and re-abstract them
                nodes = self.result.get("nodes", [])
                if len(nodes) >= 2:
                    can_abstract, _ = self.graph.can_abstract_nodes(nodes)
                    if can_abstract:
                        self.graph.AbstractNodes(nodes)
                        self.graph._simplification_history.append(
                            self.expanded_operation
                        )

            self._refresh_canvas()

    def _refresh_canvas(self):
        """Refresh the canvas to reflect graph changes."""
        mw = _get_main_window(self.canvas)
        if mw and hasattr(mw, "graph_builder_controller"):
            mw.graph_builder_controller.visualize_graph_on_canvas(self.graph)
