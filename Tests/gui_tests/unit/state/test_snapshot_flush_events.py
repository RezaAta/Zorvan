import pytest

try:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for this test")

from zorvan.GUI.graph_runner import GraphRunner


class DummyNode:
    def __init__(self):
        self.name = "n"
        self.value = 0


class DummyGraph:
    def __init__(self, nodes):
        self.nodes = nodes


def test_save_snapshot_processes_pending_qtimer(qapp):
    node = DummyNode()
    graph = DummyGraph([node])

    # Schedule a deferred update to node.value via QTimer.singleShot
    def _set_val():
        node.value = 42

    QTimer.singleShot(0, _set_val)

    runner = GraphRunner(None)
    runner.graph = graph
    # Call save_graph_snapshot which internally processes Qt events
    runner.save_graph_snapshot()
    # The save_graph_snapshot should have processed Qt events and captured the updated value
    snap = runner._graph_snapshot
    # Find node id in snapshot
    nid = id(node)
    assert nid in snap
    assert snap[nid]["value"] == 42
