import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.dialogs.replace_node_viewmodel import ReplaceNodeViewModel
from gui_framework.views.dialogs.replace_node_dialog import ReplaceNodeDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_replace_node_view_populates_and_selects(qapp):
    data = {
        "Basic": {
            "description": "Basic nodes",
            "nodes": [("A", "Add", "Adds"), ("M", "Mult", "Multiply")],
        }
    }
    vm = ReplaceNodeViewModel(data)
    vm.initialize()

    dlg = ReplaceNodeDialog(vm)
    # initial population
    assert dlg.tree_widget.topLevelItemCount() == 1

    # simulate search
    dlg.search_bar.setText("mult")
    # process events to allow binding
    from PyQt6.QtWidgets import QApplication

    QApplication.processEvents()

    # find first visible leaf and activate
    # (simulate user selection by calling internal method)
    items = []
    for i in range(dlg.tree_widget.topLevelItemCount()):
        cat = dlg.tree_widget.topLevelItem(i)
        for j in range(cat.childCount()):
            it = cat.child(j)
            if it.data(0, 0):
                items.append(it)
    assert any("Mult" in it.text(0) for it in items)
    # select and accept
    dlg._on_item_activated(items[-1])
    assert dlg.selected_type() is not None
    dlg.close()
