from PyQt6.QtWidgets import QWidget

from gui_framework.services.examples_repository import ExamplesRepository
from zorvan.GUI.controllers.dialog_controller import DialogController
from zorvan.GUI.examples_loader import ExamplesLoader


class DummyCanvas:
    def __init__(self, graph):
        self.scene = type("S", (), {"clear": lambda self: None})()
        self.node_items = {}

        # create fake items with pos() and attributes
        class Item:
            def __init__(self, x, y, color):
                self._x = x
                self._y = y
                self.manual_color = type("C", (), {"name": lambda self: color})()
                self.radius = 10

            def pos(self):
                class P:
                    def __init__(self, x, y):
                        self._x = x
                        self._y = y

                    def x(self):
                        return self._x

                    def y(self):
                        return self._y

                return P(self._x, self._y)

            def label(self):
                return None

        for i, n in enumerate(ExamplesLoader()._build_addition_chain().nodes):
            self.node_items[n] = Item(i * 10.0, i * 20.0, "#123456")


class StubMain:
    def __init__(self, repo, graph, canvas):
        self.examples_repository = repo
        self.graph = graph
        self.canvas = canvas
        self.last_loaded_example_name = "AdditionChain"
        self.status_bar = type("SB", (), {"showMessage": lambda self, m: None})()


def test_save_current_example_layout(tmp_path):
    repo = ExamplesRepository(storage_path=str(tmp_path / "layouts.json"))
    loader = ExamplesLoader()
    g = loader._build_addition_chain()

    canvas = DummyCanvas(g)
    main = StubMain(repo, g, canvas)
    dc = DialogController(main)

    ok = dc.save_current_example_layout()
    assert ok is True
    loaded = repo.load_layout("AdditionChain")
    # layout should exist and include node entries
    assert isinstance(loaded, dict)
    assert len(loaded) > 0
