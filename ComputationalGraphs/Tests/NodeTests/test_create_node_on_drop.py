import sys

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


def test_create_node_and_connect_on_drop(monkeypatch):
    app = QApplication(sys.argv)
    mw = MainWindow()

    # Build graph with one addition node
    g = mw.graph
    n1 = AdditionNode(name="add1")
    g.AddNode(n1)

    # Create NodeItem on canvas
    item1 = mw.canvas.add_node_item(n1, x=0, y=0)

    # Start a connection from this node
    mw.canvas.start_connection(item1)

    # Patch ReplaceNodeDialog to return MultiplicationNode
    class StubReplaceDialog:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return True

        def selected_type(self):
            return "MultiplicationNode"

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.replace_node_dialog.ReplaceNodeDialog",
        StubReplaceDialog,
    )

    # Simulate release on empty space by emitting the signal
    mw.canvas.connection_dropped_on_empty.emit(QPointF(200, 100), [item1])

    # There should be a new node on the canvas that is a MultiplicationNode
    found = False
    for node in mw.canvas.node_items.keys():
        if isinstance(node, MultiplicationNode):
            found = True
            created_node = node
            break
    assert found

    # And there should be an edge from add1 to the created multiplication node
    assert any(
        e.source_node.node == n1 and e.target_node.node == created_node
        for e in mw.canvas.edge_items
    )

    app.quit()


def test_drop_create_cancelled_does_not_create(monkeypatch):
    app = QApplication(sys.argv)
    mw = MainWindow()

    g = mw.graph
    n1 = AdditionNode(name="add1")
    g.AddNode(n1)
    item1 = mw.canvas.add_node_item(n1, x=0, y=0)

    mw.canvas.start_connection(item1)

    class StubReplaceDialogCancel:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return False

        def selected_type(self):
            return None

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.replace_node_dialog.ReplaceNodeDialog",
        StubReplaceDialogCancel,
    )

    initial_node_count = len(mw.canvas.node_items)
    mw.canvas.connection_dropped_on_empty.emit(QPointF(200, 100), [item1])

    assert len(mw.canvas.node_items) == initial_node_count

    app.quit()


def test_create_node_and_connect_from_selected_multiple_nodes(monkeypatch):
    app = QApplication(sys.argv)
    mw = MainWindow()

    # Build graph with two addition nodes
    g = mw.graph
    n1 = AdditionNode(name="add1")
    n2 = AdditionNode(name="add2")
    g.AddNode(n1, n2)

    # Add NodeItems to canvas
    item1 = mw.canvas.add_node_item(n1, x=0, y=0)
    item2 = mw.canvas.add_node_item(n2, x=100, y=0)

    # Select both nodes and start connection
    item1.setSelected(True)
    item2.setSelected(True)
    mw.canvas.start_connection(item1)

    # Patch ReplaceNodeDialog to return MultiplicationNode
    class StubReplaceDialog:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return True

        def selected_type(self):
            return "MultiplicationNode"

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.replace_node_dialog.ReplaceNodeDialog",
        StubReplaceDialog,
    )

    mw.canvas.connection_dropped_on_empty.emit(QPointF(200, 100), [item1, item2])

    # Confirm one new multiplication node exists
    mult_nodes = [
        n for n in mw.canvas.node_items.keys() if isinstance(n, MultiplicationNode)
    ]
    assert len(mult_nodes) == 1

    created_node = mult_nodes[0]
    # There should be edges from both add1 and add2 to the new node
    sources = {
        e.source_node.node
        for e in mw.canvas.edge_items
        if e.target_node.node == created_node
    }
    assert n1 in sources and n2 in sources

    app.quit()
