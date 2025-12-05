"""
AddEdgeCommand - Undoable command for adding an edge between nodes.
"""

from PyQt6.QtGui import QUndoCommand


class AddEdgeCommand(QUndoCommand):
    """Command to add an edge between two nodes."""

    def __init__(self, canvas, graph, source_node, target_node, description="Add Edge"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.source_node = source_node
        self.target_node = target_node

    def redo(self):
        """Add the edge to graph and canvas."""
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

        # Add the edge (add_edge_item also connects in graph)
        self.canvas.add_edge_item(self.source_node, self.target_node)

    def undo(self):
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
