"""
PasteCommand - Undoable command for pasting nodes and edges from clipboard.
"""

from PyQt6.QtGui import QUndoCommand


class PasteCommand(QUndoCommand):
    """Command to paste nodes and edges from the clipboard.

    This command stores all information needed to recreate the pasted nodes
    and edges, and can undo by removing them all.
    """

    def __init__(self, canvas, graph, pasted_nodes, pasted_edges, node_positions,
                 description="Paste"):
        """Initialize the paste command.

        Args:
            canvas: The GraphCanvas instance
            graph: The Graph instance
            pasted_nodes: List of node objects that were pasted
            pasted_edges: List of (source_node, target_node) tuples for edges
            node_positions: Dict mapping node -> (x, y) positions
        """
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.pasted_nodes = pasted_nodes
        self.pasted_edges = pasted_edges
        self.node_positions = node_positions
        self._first_redo = True

    def redo(self):
        """Add all pasted nodes and edges to graph and canvas."""
        if self._first_redo:
            # First redo is already done by the paste operation itself
            self._first_redo = False
            return

        # Re-add nodes
        for node in self.pasted_nodes:
            if node not in self.graph.nodes:
                self.graph.AddNode(node)
            if node not in self.canvas.node_items:
                x, y = self.node_positions.get(node, (0, 0))
                self.canvas.add_node_item(node, x, y)

        # Re-add edges
        for src, tgt in self.pasted_edges:
            # Check edge doesn't already exist
            edge_exists = False
            for edge in self.canvas.edge_items:
                try:
                    if edge.source_node.node == src and edge.target_node.node == tgt:
                        edge_exists = True
                        break
                except Exception:
                    pass
            if not edge_exists:
                self.canvas.add_edge_item(src, tgt)

        # Select the pasted nodes
        for it in list(self.canvas.scene.selectedItems()):
            it.setSelected(False)
        for node in self.pasted_nodes:
            node_item = self.canvas.node_items.get(node)
            if node_item:
                node_item.setSelected(True)

    def undo(self):
        """Remove all pasted nodes and edges from graph and canvas."""
        # Remove edges first
        for src, tgt in self.pasted_edges:
            self._remove_edge(src, tgt)

        # Remove nodes
        for node in self.pasted_nodes:
            self._remove_node(node)

    def _remove_edge(self, src, tgt):
        """Remove a single edge from graph and canvas."""
        for edge in list(self.canvas.edge_items):
            try:
                if edge.source_node.node == src and edge.target_node.node == tgt:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                    break
            except Exception:
                pass

        try:
            self.graph.DisconnectPreNode(tgt, src)
        except Exception:
            pass

    def _remove_node(self, node):
        """Remove a single node from graph and canvas."""
        if node in self.canvas.node_items:
            node_item = self.canvas.node_items[node]
            # Remove any remaining connected edges
            for edge in list(node_item.edges[:]):
                try:
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass
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
