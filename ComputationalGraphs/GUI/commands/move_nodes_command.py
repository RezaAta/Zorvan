"""
MoveNodesCommand - Undoable command for moving nodes on the canvas.
"""

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QUndoCommand


class MoveNodesCommand(QUndoCommand):
    """Command to move nodes on the canvas.

    Stores old and new positions for all moved nodes.
    """

    def __init__(self, canvas, node_positions, description="Move"):
        """Initialize the move command.

        Args:
            canvas: The GraphCanvas instance
            node_positions: List of tuples (node, old_pos, new_pos)
                           where positions are QPointF objects
        """
        super().__init__(description)
        self.canvas = canvas
        # Store as list of (node, old_x, old_y, new_x, new_y) for reliable serialization
        self.positions = []
        for node, old_pos, new_pos in node_positions:
            self.positions.append((
                node,
                old_pos.x(), old_pos.y(),
                new_pos.x(), new_pos.y()
            ))

    def redo(self):
        """Move nodes to their new positions."""
        for node, old_x, old_y, new_x, new_y in self.positions:
            if node in self.canvas.node_items:
                node_item = self.canvas.node_items[node]
                node_item.setPos(QPointF(new_x, new_y))
                # Update connected edges
                for edge in node_item.edges:
                    try:
                        edge.update_position()
                    except Exception:
                        pass

    def undo(self):
        """Move nodes back to their old positions."""
        for node, old_x, old_y, new_x, new_y in self.positions:
            if node in self.canvas.node_items:
                node_item = self.canvas.node_items[node]
                node_item.setPos(QPointF(old_x, old_y))
                # Update connected edges
                for edge in node_item.edges:
                    try:
                        edge.update_position()
                    except Exception:
                        pass

    def mergeWith(self, other):
        """Merge consecutive moves of the same nodes.

        This prevents flooding the undo stack with tiny move increments.
        """
        if not isinstance(other, MoveNodesCommand):
            return False

        # Check if same nodes are being moved
        my_nodes = {pos[0] for pos in self.positions}
        other_nodes = {pos[0] for pos in other.positions}

        if my_nodes != other_nodes:
            return False

        # Update our new positions with the other command's new positions
        other_pos_map = {pos[0]: (pos[3], pos[4]) for pos in other.positions}
        new_positions = []
        for node, old_x, old_y, new_x, new_y in self.positions:
            final_x, final_y = other_pos_map.get(node, (new_x, new_y))
            new_positions.append((node, old_x, old_y, final_x, final_y))
        self.positions = new_positions

        return True

    def id(self):
        """Return a unique ID for merge grouping."""
        # Use a fixed ID so consecutive moves can be merged
        return 1001  # Arbitrary unique ID for move commands
