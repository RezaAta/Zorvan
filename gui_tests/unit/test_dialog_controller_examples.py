from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMenu

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.controllers.dialog_controller import DialogController


class DummyMainWindow(QObject):
    def __init__(self, repo):
        super().__init__()
        self.examples_repository = repo
        # Add examples_loader for fallback path
        self.examples_loader = type("EL", (), {"get_categories": lambda self: []})()


class DummyRepo:
    def __init__(self):
        self._cats = {
            "Prog": [("ex1", "Desc1", lambda: None), ("ex2", "Desc2", lambda: None)]
        }

    def list_examples_by_category(self):
        return self._cats


def test_populate_examples_menu_uses_repository():
    mw = DummyMainWindow(DummyRepo())
    dc = DialogController(mw)
    menu = QMenu()
    dc.populate_examples_menu(menu)

    # There should be a top-level menu for our category
    actions = [a.text() for a in menu.actions()]
    assert "Prog" in actions

    # The submenu should contain our examples
    submenu = menu.actions()[actions.index("Prog")].menu()
    sub_actions = [a.text() for a in submenu.actions()]
    assert "ex1" in sub_actions and "ex2" in sub_actions


def test_load_example_triggers_full_reset():
    class MW:
        def __init__(self):
            self.canvas = type("C", (), {})()
            self.canvas.scene = type("S", (), {"clear": lambda self: None})()
            self.canvas.node_items = {}
            self.canvas.edge_items = {}
            self.canvas._subgraph_widgets = {}
            self.status_bar = type("SB", (), {"showMessage": lambda self, msg: None})()
            self._visualized = None
            self.reset_called = False

        def set_graph(self, g):
            self.graph = g

        def _visualize_graph_on_canvas(self, g):
            self._visualized = g

        def update_starting_nodes_display(self):
            pass

        def update_stopping_nodes_display(self):
            pass

        def apply_graph_layout(self, *a, **k):
            pass

        def _sync_graph_after_load(self):
            pass

        def reset_graph(self):
            self.reset_called = True

    mw = MW()
    dc = DialogController(mw)

    # builder returns a valid Graph instance
    def builder():
        return Graph()

    # Call load_example - should perform full reset per new behavior
    dc.load_example(builder, "dummy-example")

    assert getattr(mw, "_visualized", None) is not None
    assert mw.reset_called is True
