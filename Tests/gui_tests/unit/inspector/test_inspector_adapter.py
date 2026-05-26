import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter tests")

from gui_framework.legacy import InspectorPane
from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel


class Node:
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.predecessors = []


class Graph:
    def __init__(self, nodes):
        self.nodes = nodes


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_inspector_adapter_constructs_and_updates(qapp):
    a = Node("A")
    g = Graph([a])

    cvm = CanvasViewModel(g)
    cvm.initialize()

    pane = InspectorPane(cvm)
    view = pane.widget()

    # Select node A and notify
    cvm.select_node("A")
    cvm.nodes_changed += 1

    # Process Qt events to allow UI update
    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    # InspectorView should have some widgets for the selected node
    assert hasattr(view, "_widgets")
    assert len(view._widgets) > 0

    pane.close()
