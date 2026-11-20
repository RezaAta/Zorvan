import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(
    not PYQT, reason="PyQt6 required for NodeEditorDialog tests"
)

from gui_framework.legacy import NodeEditorDialog
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel


class DummyNode:
    def __init__(self):
        self.name = "D"
        self.value = 0


def test_set_value_via_viewmodel():
    node = DummyNode()
    vm = NodeEditorViewModel(node)
    vm.initialize()

    # Set numeric value
    ok = vm.set_value("2")
    assert ok
    assert node.value == 2

    # Set list value
    ok = vm.set_value("[1, 2]")
    assert ok
    assert node.value == [1, 2]


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_set_value_via_dialog(qapp):
    node = DummyNode()
    dlg = NodeEditorDialog(node)
    # Access underlying MVVM value widget
    val_w = dlg._dlg._widgets["value"]
    assert hasattr(val_w, "setPlainText")

    # Set to numeric
    # Set value on current widget; to be robust against a late refresh, re-fetch the widget
    val_w.setPlainText("2")
    qapp.processEvents()
    val_w2 = dlg._dlg._widgets["value"]
    val_w2.setPlainText("2")
    # Ensure widget text and VM linkage are correct
    assert val_w2.toPlainText().strip() == "2"
    assert dlg._dlg.vm is dlg._vm
    # VM should reflect new text after _on_ok
    # Instrument vm.set_value to check whether _on_ok invokes it
    calls = {}
    original_set_value = dlg._vm.set_value

    def _spy(val, _orig=original_set_value):
        calls["val"] = val
        return _orig(val)

    dlg._vm.set_value = _spy
    dlg._dlg._on_ok()
    # Confirm whether _on_ok invoked set_value
    assert "val" in calls, "_on_ok did not call vm.set_value"
    assert calls["val"].strip() == "2"
    # After spying, direct set_value should still work
    ok = original_set_value("2")
    assert ok
    assert dlg._vm.get_value() == 2
    assert node.value == 2

    # Set to list in a fresh dialog (previous dialog may have been accepted and closed)
    dlg2 = NodeEditorDialog(node)
    val_w3 = dlg2._dlg._widgets["value"]
    val_w3.setPlainText("[3, 4]")
    dlg2._dlg._on_ok()
    assert dlg2._vm.get_value() == [3, 4]
    assert node.value == [3, 4]

    dlg.close()
    dlg2.close()
