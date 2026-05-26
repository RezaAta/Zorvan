"""
MoveNodesCommand - Undoable command for moving nodes in MVVM canvas.

Integrates with CanvasViewModel to support undo/redo of node movements.
"""

try:
    from PyQt6.QtGui import QUndoCommand

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    # Stub for testing without PyQt
    class QUndoCommand:
        def __init__(self, description=""):
            pass

        def redo(self):
            pass

        def undo(self):
            pass


if PYQT_AVAILABLE:

    class MoveNodesCommand(QUndoCommand):
        """
        Command to move nodes on the canvas.

        Stores old and new positions for all moved nodes and updates the CanvasViewModel.
        """

        def __init__(self, viewmodel, node_positions, description="Move Nodes"):
            """
            Initialize the move command.

            Args:
                viewmodel: CanvasViewModel instance
                node_positions: Dict mapping node_id to (old_x, old_y, new_x, new_y) tuples
                description: Command description for undo stack
            """
            super().__init__(description)
            self.viewmodel = viewmodel
            self.positions = node_positions.copy()

        def redo(self):
            """Move nodes to their new positions."""
            new_positions = {}
            for node_id, (old_x, old_y, new_x, new_y) in self.positions.items():
                new_positions[node_id] = (new_x, new_y)

            self.viewmodel.update_node_positions(new_positions)
            print(f"[MoveNodesCommand] Redo: Moved {len(new_positions)} nodes")

        def undo(self):
            """Move nodes back to their old positions."""
            old_positions = {}
            for node_id, (old_x, old_y, new_x, new_y) in self.positions.items():
                old_positions[node_id] = (old_x, old_y)

            self.viewmodel.update_node_positions(old_positions)
            print(f"[MoveNodesCommand] Undo: Restored {len(old_positions)} nodes")

        def mergeWith(self, other):
            """
            Merge consecutive moves of the same nodes.

            This prevents flooding the undo stack with tiny move increments during dragging.
            """
            if not isinstance(other, MoveNodesCommand):
                return False

            # Check if same nodes are being moved
            if set(self.positions.keys()) != set(other.positions.keys()):
                return False

            # Update our new positions with the other command's new positions
            for node_id in self.positions:
                old_x, old_y, _, _ = self.positions[node_id]
                _, _, new_x, new_y = other.positions[node_id]
                self.positions[node_id] = (old_x, old_y, new_x, new_y)

            return True

        def id(self):
            """Return command ID for merging."""
            return 1  # All move commands have the same ID for merging

else:
    # Stub for testing
    class MoveNodesCommand:
        def __init__(self, viewmodel, node_positions, description="Move Nodes"):
            self.viewmodel = viewmodel
            self.positions = node_positions.copy()

        def redo(self):
            """Move nodes to their new positions."""
            new_positions = {}
            for node_id, (old_x, old_y, new_x, new_y) in self.positions.items():
                new_positions[node_id] = (new_x, new_y)
            self.viewmodel.update_node_positions(new_positions)

        def undo(self):
            """Move nodes back to their old positions."""
            old_positions = {}
            for node_id, (old_x, old_y, new_x, new_y) in self.positions.items():
                old_positions[node_id] = (old_x, old_y)
            self.viewmodel.update_node_positions(old_positions)

        def mergeWith(self, other):
            """Merge consecutive moves of the same nodes."""
            if not isinstance(other, MoveNodesCommand):
                return False
            if set(self.positions.keys()) != set(other.positions.keys()):
                return False
            for node_id in self.positions:
                old_x, old_y, _, _ = self.positions[node_id]
                _, _, new_x, new_y = other.positions[node_id]
                self.positions[node_id] = (old_x, old_y, new_x, new_y)
            return True
