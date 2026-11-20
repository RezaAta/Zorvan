"""
ReplaceNodeCommand - Undoable command for replacing a node with a different type.

This command replaces the underlying graph node while preserving:
- Visual position on canvas
- All predecessor/successor connections
- Manual color if set
"""

from PyQt6.QtGui import QUndoCommand


class ReplaceNodeCommand(QUndoCommand):
    """Command to replace a node with a new node of a different type.

    Stores all state needed to undo the replacement:
    - Original node object
    - New node object
    - Connection information (predecessors/successors)
    - Visual state (position, color)
    """

    def __init__(
        self,
        canvas,
        graph,
        node_item,
        old_node,
        new_node,
        description="Replace Node",
    ):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.node_item = node_item
        self.old_node = old_node
        self.new_node = new_node

        # Store position for potential restoration
        self.x = node_item.pos().x()
        self.y = node_item.pos().y()

        # Store manual color if set
        self.manual_color = getattr(node_item, "manual_color", None)

        # Store connection data: predecessors of old_node and successors
        preds = old_node.predecessors if hasattr(old_node, "predecessors") else []
        self.predecessors = list(preds)

        # Get successors from the graph's successor map
        if hasattr(graph, "BuildSuccessorMap"):
            successor_map = graph.BuildSuccessorMap()
        else:
            successor_map = {}
        self.successors = list(successor_map.get(old_node, []))

        # Track if this is the first redo (command just created)
        # When already_performed=True, the replacement was done before command push
        self._first_redo = True
        self._already_performed = False

    def mark_already_performed(self):
        """Mark that the replacement was already performed before push.

        Call this when the replacement was done externally (e.g., by
        replace_node_item) before the command was pushed to the stack.
        """
        self._already_performed = True

    def redo(self):
        """Perform the node replacement."""
        if self._first_redo and self._already_performed:
            # On first redo when already performed, just skip
            self._first_redo = False
            return

        self._first_redo = False
        # Perform the replacement
        self._perform_replacement(self.old_node, self.new_node)

    def undo(self):
        """Undo the node replacement - restore original node."""
        self._perform_replacement(self.new_node, self.old_node)

    def _update_node_items_mapping(self, old_node, new_node):
        """Update the canvas node_items dictionary mapping."""
        if old_node in self.canvas.node_items:
            del self.canvas.node_items[old_node]
        self.canvas.node_items[new_node] = self.node_item

    def _perform_replacement(self, from_node, to_node):
        """Perform replacement from from_node to to_node."""
        # Use graph's ReplaceNode if available
        if hasattr(self.graph, "ReplaceNode") and from_node in self.graph.nodes:
            try:
                self.graph.ReplaceNode(to_node, from_node)
            except Exception:
                # Fallback: manual replacement
                self._manual_graph_replace(from_node, to_node)
        else:
            self._manual_graph_replace(from_node, to_node)

        # Update node_items mapping
        self._update_node_items_mapping(from_node, to_node)

        # Update the NodeItem reference
        self.node_item.node = to_node

        # Update visual display
        try:
            self.node_item.set_label_text(getattr(to_node, "name", ""))
        except Exception:
            try:
                self.node_item.label.setPlainText(getattr(to_node, "name", ""))
            except Exception:
                pass

        try:
            self.node_item.update_value_display()
        except Exception:
            pass

        # Restore manual color if set
        if self.manual_color is not None:
            try:
                self.node_item.set_manual_color(self.manual_color)
            except Exception:
                self.node_item.manual_color = self.manual_color
                self.node_item.update()

        # Update connected edges to reflect the new node
        self._update_edge_references(from_node, to_node)

    def _manual_graph_replace(self, from_node, to_node):
        """Manually replace node in graph if ReplaceNode is not available."""
        self._remove_from_graph(from_node)
        self._add_to_graph(to_node)
        self._restore_predecessor_connections(to_node)
        self._restore_successor_connections(to_node)

    def _remove_from_graph(self, node):
        """Remove a node from the graph."""
        if node not in self.graph.nodes:
            return
        try:
            self.graph.RemoveNode(node)
        except Exception:
            try:
                self.graph.nodes.remove(node)
            except Exception:
                pass

    def _add_to_graph(self, node):
        """Add a node to the graph."""
        if node in self.graph.nodes:
            return
        try:
            self.graph.AddNode(node)
        except Exception:
            self.graph.nodes.append(node)

    def _restore_predecessor_connections(self, to_node):
        """Connect predecessors to the new node."""
        for pred in self.predecessors:
            if pred not in self.graph.nodes:
                continue
            try:
                self.graph.ConnectPreNode(to_node, pred)
            except Exception:
                if hasattr(to_node, "AddPreNode"):
                    to_node.AddPreNode(pred)

    def _restore_successor_connections(self, to_node):
        """Connect the new node as predecessor to successors."""
        for succ in self.successors:
            if succ not in self.graph.nodes:
                continue
            try:
                self.graph.ConnectPreNode(succ, to_node)
            except Exception:
                if hasattr(succ, "AddPreNode"):
                    succ.AddPreNode(to_node)

    def _update_edge_references(self, from_node, to_node):
        """Update edge items to reference the new node."""
        for edge in list(self.canvas.edge_items):
            try:
                # Update source reference if needed
                if edge.source_node == self.node_item:
                    # Edge already references node_item, which now has to_node
                    edge.update()
                # Update target reference if needed
                if edge.target_node == self.node_item:
                    edge.update()
            except Exception:
                pass
