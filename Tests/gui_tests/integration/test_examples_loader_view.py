import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False


from gui_framework.viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel
from gui_framework.views.examples_loader_view import ExamplesLoaderView


class DummyRepo:
    def __init__(self):
        self._examples = {
            "ex1": (lambda: "built1", "Example 1"),
            "ex2": (lambda: None, "Broken example"),
        }

    def list_examples(self):
        return self._examples

    def build(self, name):
        return self._examples[name][0]()


@pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 not installed")
def test_examples_loader_view_loads_and_displays_preview(qtbot):
    app = QApplication.instance() or QApplication([])
    repo = DummyRepo()
    vm = ExamplesLoaderViewModel(repository=repo)
    view = ExamplesLoaderView(vm)
    qtbot.addWidget(view)

    # initial tree should show category and child items
    top_items = [
        view.tree.topLevelItem(i).text(0) for i in range(view.tree.topLevelItemCount())
    ]
    assert "Prog" in top_items

    # find child items under Prog
    prog_index = top_items.index("Prog")
    prog_item = view.tree.topLevelItem(prog_index)
    child_names = [prog_item.child(i).text(0) for i in range(prog_item.childCount())]
    assert "ex1" in child_names and "ex2" in child_names

    # select ex1 and ensure preview updates
    # set current item to ex1 child
    for i in range(prog_item.childCount()):
        if prog_item.child(i).text(0) == "ex1":
            view.tree.setCurrentItem(prog_item.child(i))
            break
    app.processEvents()
    assert view.preview.text() == "Example 1"

    # load ex1 (builder returns a value)
    view.load_btn.click()
    app.processEvents()
    assert view.preview.text() == "Loaded: ex1"

    # select ex2 and try to load (builder returns None)
    for i in range(prog_item.childCount()):
        if prog_item.child(i).text(0) == "ex2":
            view.tree.setCurrentItem(prog_item.child(i))
            break
    app.processEvents()
    assert view.preview.text() == "Broken example"
    view.load_btn.click()
    app.processEvents()
    assert view.preview.text().startswith("Failed to load: ex2")
