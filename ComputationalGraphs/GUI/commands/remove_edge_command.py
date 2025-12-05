"""
RemoveEdgeCommand - Undoable command for removing an edge.
"""

from PyQt6.QtGui import QUndoCommand


class RemoveEdgeCommand(QUndoCommand):
    """Command to remove an edge between two nodes."""

    def __init__(
        self, canvas, graph, source_node, target_node, description="Remove Edge"
    ):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.source_node = source_node
        self.target_node = target_node

    def redo(self):
        """Remove the edge from graph and canvas."""
        # Find and remove the visual edge
        for edge in list(self.canvas.edge_items):
            try:
                if (
                    edge.source_node.node == self.source_node
                    and edge.target_node.node == self.target_node
                ):
                    edge.remove()
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                    break
            except Exception:
                pass

        # Disconnect in graph
        try:
            self.graph.DisconnectPreNode(self.target_node, self.source_node)
        except Exception:
            pass

    def undo(self):
        """Restore the edge to graph and canvas."""
        # Check both nodes exist in canvas
        if self.source_node not in self.canvas.node_items:
            return
        if self.target_node not in self.canvas.node_items:
            return

        # Check edge doesn't already exist
        for edge in self.canvas.edge_items:
            try:
                if (
                    edge.source_node.node == self.source_node
                    and edge.target_node.node == self.target_node
                ):
                    return  # Already exists
            except Exception:
                pass

        # Add edge back (this also connects in graph)
        self.canvas.add_edge_item(self.source_node, self.target_node)
