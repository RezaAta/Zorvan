from unittest.mock import MagicMock

from zorvan.Core.Graph import Graph
from zorvan.GUI.controllers.file_io_controller import FileIOController


class DummyCanvas:
    def __init__(self):
        self.scene = MagicMock()
        self.node_items = {}
        self.edge_items = {}
        self._subgraph_widgets = {}

    def update_subgraph_controls(self):
        self.subgraph_controls_updated = True


class DummyStatusBar:
    def __init__(self):
        self.last = None

    def showMessage(self, msg):
        self.last = msg


class DummyMainWindow:
    def __init__(self):
        self.canvas = DummyCanvas()
        self.status_bar = DummyStatusBar()
        self.reset_called = False
        self.graph = None

    def set_graph(self, g):
        self.graph = g

    def _visualize_graph_on_canvas(self, g):
        self.visualized = g

    def update_starting_nodes_display(self):
        pass

    def update_stopping_nodes_display(self):
        pass

    def update_graph_selector(self):
        pass

    def reset_graph(self):
        # mark that reset_graph was invoked
        self.reset_called = True


def test_apply_loaded_graph_resets_execution_controls():
    mw = DummyMainWindow()
    controller = FileIOController(mw)

    g = Graph()
    controller._apply_loaded_graph(g, "dummy.drawio")

    # GUI should have visualized the graph and performed a reset
    assert getattr(mw, "visualized", None) is g
    assert mw.reset_called is True
