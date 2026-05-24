"""
AddNodeCommand - Undoable command for adding a node to the canvas.
"""

from PyQt6.QtGui import QUndoCommand


class AddNodeCommand(QUndoCommand):
    """Command to add a node to the graph and canvas."""

    def __init__(self, canvas, graph, node, x, y, description="Add Node"):
        super().__init__(description)
        self.canvas = canvas
        self.graph = graph
        self.node = node
        self.x = x
        self.y = y
        self._first_redo = True

    def redo(self):
        """Add the node to graph and canvas."""
        # Add to graph
        if self.node not in self.graph.nodes:
            self.graph.AddNode(self.node)

        # Add to canvas if not already there
        if self.node not in self.canvas.node_items:
            self.canvas.add_node_item(self.node, self.x, self.y)

    def undo(self):
        """Remove the node from graph and canvas."""
        # Remove from canvas
        if self.node in self.canvas.node_items:
            node_item = self.canvas.node_items[self.node]

            # Remove connected edges first
            for edge in list(node_item.edges[:]):
                try:
                    src = edge.source_node.node
                    tgt = edge.target_node.node
                    # Disconnect in graph
                    try:
                        self.graph.DisconnectPreNode(tgt, src)
                    except Exception:
                        pass
                    # Remove visual edge
                    try:
                        edge.remove()
                    except Exception:
                        try:
                            self.canvas.scene.removeItem(edge)
                        except Exception:
                            pass
                    if edge in self.canvas.edge_items:
                        self.canvas.edge_items.remove(edge)
                except Exception:
                    pass

            # Remove node item from scene
            try:
                self.canvas.scene.removeItem(node_item)
            except Exception:
                pass
            del self.canvas.node_items[self.node]

        # Remove from graph
        if self.node in self.graph.nodes:
            try:
                self.graph.RemoveNode(self.node)
            except Exception:
                # If RemoveNode doesn't exist, remove from nodes list directly
                try:
                    self.graph.nodes.remove(self.node)
                except Exception:
                    pass
