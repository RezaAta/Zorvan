import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.graph_canvas import GraphCanvas
from zorvan.Nodes.AdditionNode import AdditionNode


@pytest.fixture
def setup_canvas():
    """Create a GraphCanvas with a Graph and mock undo stack for testing."""
    from PyQt6.QtGui import QUndoStack

    canvas = GraphCanvas()
    graph = getattr(canvas, "graph", None)

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


def test_connect_to_self_single_node(setup_canvas):
    canvas, graph, undo_stack = setup_canvas

    # Add a single node and its NodeItem
    node = AdditionNode(name="SingleSelf")
    graph.AddNode(node)
    ni = canvas.add_node_item(node, 10, 10)

    # Ensure it's not selected (we expect the method to select it if none selected)
    if ni.isSelected():
        ni.setSelected(False)

    # Call the helper directly (simulates choosing the menu action)
    ni._connect_selection_to_self()

    # There should be an edge from node -> node
    found = any(
        getattr(edge.source_node, "node", None) == node
        and getattr(edge.target_node, "node", None) == node
        for edge in canvas.edge_items
    )
    assert found, "Expected a self-loop edge for the single node"


def test_connect_to_self_multiple_nodes_and_undo(setup_canvas):
    canvas, graph, undo_stack = setup_canvas

    # Add two nodes
    n1 = AdditionNode(name="N1")
    n2 = AdditionNode(name="N2")
    graph.AddNode(n1)
    graph.AddNode(n2)
    ni1 = canvas.add_node_item(n1, 0, 0)
    ni2 = canvas.add_node_item(n2, 50, 0)

    # Select both
    ni1.setSelected(True)
    ni2.setSelected(True)

    # Call the helper from one of them
    ni1._connect_selection_to_self()

    # Both nodes should have self-loop edges
    has_n1 = any(
        getattr(edge.source_node, "node", None) == n1
        and getattr(edge.target_node, "node", None) == n1
        for edge in canvas.edge_items
    )
    has_n2 = any(
        getattr(edge.source_node, "node", None) == n2
        and getattr(edge.target_node, "node", None) == n2
        for edge in canvas.edge_items
    )

    assert has_n1 and has_n2, "Expected self-loop edges for both selected nodes"

    # Undo the two additions (two AddEdgeCommands should have been pushed)
    undo_stack.undo()
    undo_stack.undo()

    # Now edges should be removed
    still_n1 = any(
        getattr(edge.source_node, "node", None) == n1
        and getattr(edge.target_node, "node", None) == n1
        for edge in canvas.edge_items
    )
    still_n2 = any(
        getattr(edge.source_node, "node", None) == n2
        and getattr(edge.target_node, "node", None) == n2
        for edge in canvas.edge_items
    )

    assert (
        not still_n1 and not still_n2
    ), "Expected self-loop edges to be removed after undo"


def test_connect_to_self_does_not_show_modal(setup_canvas, monkeypatch):
    canvas, graph, undo_stack = setup_canvas

    # Patch QMessageBox methods to detect any modal calls
    called = {"info": False, "warn": False}

    try:
        from PyQt6.QtWidgets import QMessageBox

        def fake_info(*args, **kwargs):
            called["info"] = True

        def fake_warn(*args, **kwargs):
            called["warn"] = True

        monkeypatch.setattr(
            "PyQt6.QtWidgets.QMessageBox.information", fake_info, raising=False
        )
        monkeypatch.setattr(
            "PyQt6.QtWidgets.QMessageBox.warning", fake_warn, raising=False
        )
    except Exception:
        # If QMessageBox isn't available for some reason, the test environment won't exercise GUI anyway
        pass

    node = AdditionNode(name="ModalCheck")
    graph.AddNode(node)
    ni = canvas.add_node_item(node, 10, 10)

    # Ensure it's not selected so helper selects it internally
    if ni.isSelected():
        ni.setSelected(False)

    ni._connect_selection_to_self()

    # No modal dialogs should have been shown by the debug cleanup
    assert (
        not called["info"] and not called["warn"]
    ), "Connect-to-self should not show modal debug dialogs"
