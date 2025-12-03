import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


def test_replace_multiple_selected_nodes(monkeypatch):
    app = QApplication(sys.argv)
    mw = MainWindow()

    # Build graph with two addition nodes
    g = mw.graph
    n1 = AdditionNode(name="add1")
    n2 = AdditionNode(name="add2")
    g.AddNode(n1, n2)

    # Add NodeItems to canvas
    item1 = mw.canvas.add_node_item(n1, x=0, y=0)
    item2 = mw.canvas.add_node_item(n2, x=200, y=0)

    # Select both nodes in the scene
    item1.setSelected(True)
    item2.setSelected(True)

    # Patch ReplaceNodeDialog to simulate dialog returning MultiplicationNode selection
    class StubReplaceDialog:
        def __init__(self, parent=None):
            self._parent = parent

        def exec(self):
            return True

        def selected_type(self):
            return "MultiplicationNode"

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.replace_node_dialog.ReplaceNodeDialog", StubReplaceDialog
    )

    # Invoke replace on one selected item - should replace both
    mw.replace_node(item1)

    # Assert both are replaced to MultiplicationNode
    assert isinstance(item1.node, MultiplicationNode)
    assert isinstance(item2.node, MultiplicationNode)
    assert mw.status_bar.currentMessage() == "Replaced 2 node(s) with type 'MultiplicationNode'"

    app.quit()


def test_replace_single_shows_node_editor(monkeypatch):
    app = QApplication(sys.argv)
    mw = MainWindow()

    # Build graph with one addition node
    g = mw.graph
    n1 = AdditionNode(name="add1")
    g.AddNode(n1)

    # Create NodeItem on canvas
    item1 = mw.canvas.add_node_item(n1, x=0, y=0)

    # Select only one node
    item1.setSelected(True)

    # Patch ReplaceNodeDialog to return MultiplicationNode
    class StubReplaceDialog:
        def __init__(self, parent=None):
            pass
        def exec(self):
            return True
        def selected_type(self):
            return "MultiplicationNode"

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.replace_node_dialog.ReplaceNodeDialog", StubReplaceDialog
    )

    # Patch NodeEditorDialog to capture exec calls
    called = {"exec": False}

    class StubNodeEditorDialog:
        def __init__(self, node, parent=None):
            self.node = node
        def exec(self):
            called["exec"] = True
            return True

    monkeypatch.setattr(
        "ComputationalGraphs.GUI.node_editor_dialog.NodeEditorDialog", StubNodeEditorDialog
    )

    mw.replace_node(item1)

    assert called["exec"] is True
    assert mw.status_bar.currentMessage() == "Replaced node with type 'MultiplicationNode'"

    app.quit()
