"""
RemoveItemsCommand - Undoable command for removing nodes and edges from the canvas.
"""

from PyQt6.QtGui import QUndoCommand


class RemoveItemsCommand(QUndoCommand):
    """Command to remove selected nodes and edges from the graph and canvas."""

    def __init__(self, canvas, graph, node_items, edge_items, description="Delete"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph

        # Store node data for restoration: (node, x, y, manual_color)
        self.removed_nodes = []
        for node_item in node_items:
            node = node_item.node
            pos = node_item.pos()
            manual_color = getattr(node_item, "manual_color", None)
            self.removed_nodes.append((node, pos.x(), pos.y(), manual_color))

        # Store edge data for restoration: (source_node, target_node)
        self.removed_edges = []
        for edge_item in edge_items:
            try:
                src = edge_item.source_node.node
                tgt = edge_item.target_node.node
                self.removed_edges.append((src, tgt))
            except Exception:
                pass

        # Also capture edges connected to removed nodes
        for node_item in node_items:
            for edge in list(node_item.edges[:]):
                try:
                    src = edge.source_node.node
                    tgt = edge.target_node.node
                    edge_tuple = (src, tgt)
                    if edge_tuple not in self.removed_edges:
                        self.removed_edges.append(edge_tuple)
                except Exception:
                    pass

    def redo(self):
        """Remove the items from graph and canvas."""
        # Remove edges first
        for src, tgt in self.removed_edges:
            self._remove_edge(src, tgt)

        # Remove nodes
        for node, x, y, manual_color in self.removed_nodes:
            self._remove_node(node)

    def undo(self):
        """Restore the removed items to graph and canvas."""
        # Restore nodes first
        for node, x, y, manual_color in self.removed_nodes:
            self._restore_node(node, x, y, manual_color)

        # Restore edges
        for src, tgt in self.removed_edges:
            self._restore_edge(src, tgt)

    def _remove_edge(self, src, tgt):
        """Remove a single edge from graph and canvas."""
        # Find and remove the visual edge
        for edge in list(self.canvas.edge_items):
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                    break
            except Exception:
                pass

        # Disconnect in graph
        try:
            self.graph.DisconnectPreNode(tgt, src)
        except Exception:
            pass

    def _remove_node(self, node):
        """Remove a single node from graph and canvas."""
        if node in self.canvas.node_items:
            node_item = self.canvas.node_items[node]
            try:
                self.canvas.scene.removeItem(node_item)
            except Exception:
                pass
            del self.canvas.node_items[node]

        if node in self.graph.nodes:
            try:
                self.graph.RemoveNode(node)
            except Exception:
                try:
                    self.graph.nodes.remove(node)
                except Exception:
                    pass

    def _restore_node(self, node, x, y, manual_color):
        """Restore a node to graph and canvas."""
        # Add back to graph
        if node not in self.graph.nodes:
            self.graph.AddNode(node)

        # Add back to canvas
        if node not in self.canvas.node_items:
            node_item = self.canvas.add_node_item(node, x, y)
            if manual_color is not None and node_item is not None:
                try:
                    node_item.set_manual_color(manual_color)
                except Exception:
                    node_item.manual_color = manual_color
                    node_item.update()

    def _restore_edge(self, src, tgt):
        """Restore an edge to graph and canvas."""
        # Check both nodes exist in canvas
        if src not in self.canvas.node_items or tgt not in self.canvas.node_items:
            return

        # Check edge doesn't already exist
        for edge in self.canvas.edge_items:
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    return  # Already exists
            except Exception:
                pass

        # Add edge (this also connects in graph)
        self.canvas.add_edge_item(src, tgt)
