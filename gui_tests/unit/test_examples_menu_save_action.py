from PyQt6.QtWidgets import QMenu

from gui_framework.services.examples_repository import ExamplesRepository
from zorvan.GUI.controllers.dialog_controller import DialogController
from zorvan.GUI.examples_loader import ExamplesLoader


class DummyMainWindow:
    def __init__(self):
        self.examples_repository = ExamplesRepository()
        self.examples_loader = ExamplesLoader()


def test_populate_examples_menu_contains_save_action(qtbot):
    mw = DummyMainWindow()
    dc = DialogController(mw)
    menu = QMenu()
    dc.populate_examples_menu(menu)

    texts = [a.text() for a in menu.actions()]
    assert "Save Current Layout" in texts

    # Trigger the action to ensure it doesn't raise (no example loaded so warns and returns False)
    idx = texts.index("Save Current Layout")
    action = menu.actions()[idx]
    # Should be callable without exception
    action.trigger()
