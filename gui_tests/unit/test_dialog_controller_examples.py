from PyQt6.QtWidgets import QMenu

from ComputationalGraphs.GUI.controllers.dialog_controller import DialogController


class DummyMainWindow:
    def __init__(self, repo):
        self.examples_repository = repo


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
