"""
Test for undo/redo functionality in the GUI.

This test verifies that:
1. Adding a node can be undone/redone
2. Deleting nodes can be undone/redone
3. Adding edges can be undone/redone
4. Moving nodes can be undone/redone
"""

import sys
import pytest

# Skip if PyQt6 is not available
pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.commands import (
    AddEdgeCommand,
    AddNodeCommand,
    MoveNodesCommand,
    RemoveItemsCommand,
)
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def setup_canvas(app):
    """Create a GraphCanvas with a Graph for testing."""
    from ComputationalGraphs.GUI.graph_canvas import GraphCanvas
    from PyQt6.QtGui import QUndoStack

    canvas = GraphCanvas()
    graph = Graph()
    canvas.graph = graph

    # Create a mock undo stack
    undo_stack = QUndoStack()

    # Simulate having a main window with undo_stack
    class MockMainWindow:
        def __init__(self):
            self.undo_stack = undo_stack

    canvas._parent_window = MockMainWindow()

    # Override _get_undo_stack to return our mock
    original_get_undo_stack = canvas._get_undo_stack

    def mock_get_undo_stack():
        return undo_stack

    canvas._get_undo_stack = mock_get_undo_stack

    yield canvas, graph, undo_stack

    # Cleanup
    canvas._get_undo_stack = original_get_undo_stack
    canvas.close()


class TestAddNodeCommand:
    """Tests for AddNodeCommand."""

    def test_add_node_redo(self, setup_canvas):
        """Test that adding a node works correctly."""
        canvas, graph, undo_stack = setup_canvas

        node = AdditionNode(name="TestAdd")
        cmd = AddNodeCommand(canvas, graph, node, 100, 200)

        # Execute the command
        undo_stack.push(cmd)

        # Verify node was added
        assert node in graph.nodes
        assert node in canvas.node_items

    def test_add_node_undo(self, setup_canvas):
        """Test that undoing add node removes it."""
        canvas, graph, undo_stack = setup_canvas

        node = AdditionNode(name="TestAdd2")
        cmd = AddNodeCommand(canvas, graph, node, 100, 200)

        undo_stack.push(cmd)
        assert node in graph.nodes

        # Undo
        undo_stack.undo()

        # Verify node was removed
        assert node not in graph.nodes
        assert node not in canvas.node_items

    def test_add_node_redo_after_undo(self, setup_canvas):
        """Test that redo after undo restores the node."""
        canvas, graph, undo_stack = setup_canvas

        node = AdditionNode(name="TestAdd3")
        cmd = AddNodeCommand(canvas, graph, node, 100, 200)

        undo_stack.push(cmd)
        undo_stack.undo()
        undo_stack.redo()

        # Verify node was restored
        assert node in graph.nodes
        assert node in canvas.node_items


class TestRemoveItemsCommand:
    """Tests for RemoveItemsCommand."""

    def test_remove_node_redo(self, setup_canvas):
        """Test that removing a node works correctly."""
        canvas, graph, undo_stack = setup_canvas

        # First add a node
        node = ContainerNode(name="ToRemove")
        graph.AddNode(node)
        node_item = canvas.add_node_item(node, 50, 50)

        # Create remove command
        cmd = RemoveItemsCommand(canvas, graph, [node_item], [])

        # Execute
        undo_stack.push(cmd)

        # Verify node was removed
        assert node not in canvas.node_items

    def test_remove_node_undo(self, setup_canvas):
        """Test that undoing remove restores the node."""
        canvas, graph, undo_stack = setup_canvas

        # First add a node
        node = ContainerNode(name="ToRemove2")
        graph.AddNode(node)
        node_item = canvas.add_node_item(node, 50, 50)

        # Create and execute remove command
        cmd = RemoveItemsCommand(canvas, graph, [node_item], [])
        undo_stack.push(cmd)

        # Undo
        undo_stack.undo()

        # Verify node was restored
        assert node in canvas.node_items


class TestAddEdgeCommand:
    """Tests for AddEdgeCommand."""

    def test_add_edge_redo(self, setup_canvas):
        """Test that adding an edge works correctly."""
        canvas, graph, undo_stack = setup_canvas

        # Add two nodes
        node1 = AdditionNode(name="Source")
        node2 = AdditionNode(name="Target")
        graph.AddNode(node1)
        graph.AddNode(node2)
        canvas.add_node_item(node1, 0, 0)
        canvas.add_node_item(node2, 100, 0)

        # Create edge command
        cmd = AddEdgeCommand(canvas, graph, node1, node2)
        undo_stack.push(cmd)

        # Verify edge was created
        assert len(canvas.edge_items) >= 1

    def test_add_edge_undo(self, setup_canvas):
        """Test that undoing add edge removes it."""
        canvas, graph, undo_stack = setup_canvas

        # Add two nodes
        node1 = AdditionNode(name="Source2")
        node2 = AdditionNode(name="Target2")
        graph.AddNode(node1)
        graph.AddNode(node2)
        canvas.add_node_item(node1, 0, 0)
        canvas.add_node_item(node2, 100, 0)

        initial_edge_count = len(canvas.edge_items)

        # Create and execute edge command
        cmd = AddEdgeCommand(canvas, graph, node1, node2)
        undo_stack.push(cmd)

        # Undo
        undo_stack.undo()

        # Verify edge was removed
        assert len(canvas.edge_items) == initial_edge_count


class TestMoveNodesCommand:
    """Tests for MoveNodesCommand."""

    def test_move_node_redo(self, setup_canvas):
        """Test that moving a node works correctly."""
        canvas, graph, undo_stack = setup_canvas

        # Add a node
        node = AdditionNode(name="ToMove")
        graph.AddNode(node)
        node_item = canvas.add_node_item(node, 0, 0)

        old_pos = QPointF(0, 0)
        new_pos = QPointF(200, 200)

        # Create move command
        cmd = MoveNodesCommand(canvas, [(node, old_pos, new_pos)])
        undo_stack.push(cmd)

        # Verify position changed
        assert abs(node_item.pos().x() - 200) < 1
        assert abs(node_item.pos().y() - 200) < 1

    def test_move_node_undo(self, setup_canvas):
        """Test that undoing move restores position."""
        canvas, graph, undo_stack = setup_canvas

        # Add a node
        node = AdditionNode(name="ToMove2")
        graph.AddNode(node)
        node_item = canvas.add_node_item(node, 50, 50)

        old_pos = QPointF(50, 50)
        new_pos = QPointF(300, 300)

        # Create and execute move command
        cmd = MoveNodesCommand(canvas, [(node, old_pos, new_pos)])
        undo_stack.push(cmd)

        # Undo
        undo_stack.undo()

        # Verify position was restored
        assert abs(node_item.pos().x() - 50) < 1
        assert abs(node_item.pos().y() - 50) < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
