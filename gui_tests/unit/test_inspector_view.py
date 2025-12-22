import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel
from gui_framework.viewmodels.inspector_viewmodel import InspectorViewModel
from gui_framework.views.inspector_view import InspectorView


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


def test_inspector_view_populates(qapp):
    a = Node("A")
    g = Graph([a])

    cvm = CanvasViewModel(g)
    cvm.initialize()

    inspector_vm = InspectorViewModel(cvm)
    inspector_vm.initialize()

    view = InspectorView(inspector_vm)

    cvm.select_node("A")
    cvm.nodes_changed += 1

    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    assert len(view._widgets) > 0

    view.close()
