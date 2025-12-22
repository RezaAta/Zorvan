"""PyQt-based unit tests for PredecessorsDialog view."""

import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required")

from gui_framework.viewmodels.dialogs.predecessors_viewmodel import (
    PredecessorsViewModel,
)
from gui_framework.views.dialogs.predecessors_dialog import PredecessorsDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class DummyNode:
    def __init__(self, name):
        self.name = name
        self.predecessors = []


class DummyCanvas:
    def __init__(self):
        self.edge_items = []
        self.graph = None


class NodeItem:
    def __init__(self, node):
        self.node = node


def test_predecessors_dialog_renders_and_disconnects(qapp):
    a = DummyNode("A")
    b = DummyNode("B")
    a.predecessors = [b]
    canvas = DummyCanvas()

    class DummyGraph:
        def __init__(self, nodes):
            self.nodes = nodes
            self.idToNodeDictionary = {}

        def DisconnectPreNode(self, node, pred):
            try:
                node.predecessors = [
                    p
                    for p in node.predecessors
                    if p is not pred
                    and getattr(p, "name", None) != getattr(pred, "name", None)
                ]
            except Exception:
                pass

    canvas.graph = DummyGraph([a, b])

    vm = PredecessorsViewModel(node_item=NodeItem(a), canvas=canvas)
    dlg = PredecessorsDialog(vm)

    # Let the BaseView binding happen (QTimer singleShot) and process events
    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    # Initially one item in list
    assert dlg.list_widget.count() == 1

    # Select it and disconnect
    dlg.list_widget.setCurrentRow(0)
    dlg._on_disconnect()
    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    # After disconnect, list should be empty (model refreshed)
    assert dlg.list_widget.count() == 0

    dlg.close()
