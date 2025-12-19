"""
Unit tests for Canvas Commands (Stage 3).

Tests the command system for undo/redo support without requiring PyQt.
"""

import pytest

from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel


class MockNode:
    """Mock computational graph node for testing."""
    
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.predecessors = []


class MockGraph:
    """Mock computational graph for testing."""
    
    def __init__(self):
        self.nodes = []


@pytest.fixture
def viewmodel():
    """Create a CanvasViewModel with a simple graph."""
    graph = MockGraph()
    
    node_a = MockNode("A", 0, 0)
    node_b = MockNode("B", 100, 0)
    node_c = MockNode("C", 50, 100)
    
    graph.nodes = [node_a, node_b, node_c]
    
    vm = CanvasViewModel(graph)
    vm.initialize()
    return vm


class TestMoveNodesCommand:
    """Test MoveNodesCommand for undo/redo of node movements."""
    
    def test_move_command_stores_positions(self, viewmodel):
        """Test that move command stores old and new positions."""
        from gui_framework.commands import MoveNodesCommand
        
        positions = {
            "A": (0, 0, 50, 50),
            "B": (100, 0, 150, 50)
        }
        
        command = MoveNodesCommand(viewmodel, positions)
        
        assert command.positions == positions
        assert command.viewmodel == viewmodel
    
    def test_move_command_redo(self, viewmodel):
        """Test that redo moves nodes to new positions."""
        from gui_framework.commands import MoveNodesCommand
        
        positions = {
            "A": (0, 0, 50, 50)
        }
        
        command = MoveNodesCommand(viewmodel, positions)
        command.redo()
        
        node_a = viewmodel.get_node("A")
        assert node_a.x == 50
        assert node_a.y == 50
    
    def test_move_command_undo(self, viewmodel):
        """Test that undo moves nodes back to old positions."""
        from gui_framework.commands import MoveNodesCommand
        
        positions = {
            "A": (0, 0, 50, 50)
        }
        
        command = MoveNodesCommand(viewmodel, positions)
        command.redo()
        
        assert viewmodel.get_node("A").x == 50
        
        command.undo()
        
        assert viewmodel.get_node("A").x == 0
        assert viewmodel.get_node("A").y == 0
    
    def test_move_command_multiple_nodes(self, viewmodel):
        """Test moving multiple nodes at once."""
        from gui_framework.commands import MoveNodesCommand
        
        positions = {
            "A": (0, 0, 10, 10),
            "B": (100, 0, 110, 10),
            "C": (50, 100, 60, 110)
        }
        
        command = MoveNodesCommand(viewmodel, positions)
        command.redo()
        
        assert viewmodel.get_node("A").x == 10
        assert viewmodel.get_node("B").x == 110
        assert viewmodel.get_node("C").x == 60
        
        command.undo()
        
        assert viewmodel.get_node("A").x == 0
        assert viewmodel.get_node("B").x == 100
        assert viewmodel.get_node("C").x == 50
    
    def test_move_command_merge(self, viewmodel):
        """Test that consecutive moves of same nodes can merge."""
        from gui_framework.commands import MoveNodesCommand
        
        # First move
        command1 = MoveNodesCommand(viewmodel, {"A": (0, 0, 10, 10)})
        
        # Second move of same node
        command2 = MoveNodesCommand(viewmodel, {"A": (10, 10, 20, 20)})
        
        # Merge should succeed
        assert command1.mergeWith(command2) is True
        
        # Command1 should now have the final position
        assert command1.positions["A"] == (0, 0, 20, 20)
    
    def test_move_command_merge_different_nodes(self, viewmodel):
        """Test that moves of different nodes don't merge."""
        from gui_framework.commands import MoveNodesCommand
        
        command1 = MoveNodesCommand(viewmodel, {"A": (0, 0, 10, 10)})
        command2 = MoveNodesCommand(viewmodel, {"B": (100, 0, 110, 10)})
        
        # Merge should fail (different nodes)
        assert command1.mergeWith(command2) is False


class TestDeleteItemsCommand:
    """Test DeleteItemsCommand (placeholder for Stage 3)."""
    
    def test_delete_command_creation(self, viewmodel):
        """Test creating a delete command."""
        from gui_framework.commands import DeleteItemsCommand
        
        command = DeleteItemsCommand(viewmodel, ["A", "B"], ["edge1"])
        
        assert command.node_ids == ["A", "B"]
        assert command.edge_ids == ["edge1"]
        assert command.viewmodel == viewmodel
    
    def test_delete_command_redo_placeholder(self, viewmodel):
        """Test that delete redo is a placeholder (doesn't crash)."""
        from gui_framework.commands import DeleteItemsCommand
        
        command = DeleteItemsCommand(viewmodel, ["A"])
        
        # Should not crash (placeholder implementation)
        command.redo()
        
        # Nodes should still exist (placeholder doesn't actually delete)
        assert viewmodel.get_node("A") is not None
    
    def test_delete_command_undo_placeholder(self, viewmodel):
        """Test that delete undo is a placeholder (doesn't crash)."""
        from gui_framework.commands import DeleteItemsCommand
        
        command = DeleteItemsCommand(viewmodel, ["A"])
        command.redo()
        
        # Should not crash (placeholder implementation)
        command.undo()
        
        # Nodes should still exist (placeholder doesn't actually delete)
        assert viewmodel.get_node("A") is not None
