import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(
    not PYQT, reason="PyQt6 required for some NodeEditorDialog tests"
)

from gui_framework.viewmodels.dialogs.node_editor_viewmodel import (
    NodeEditorViewModel as DialogNodeEditorViewModel,
)
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.legacy import NodeEditorDialog


class DummyNode:
    def __init__(self):
        self.value = 5
        self.user_locked_value = True


def test_viewmodel_preserves_value_on_empty_assignment():
    node = DummyNode()
    vm = NodeEditorViewModel(node)
    vm.initialize()

    # Attempt to set empty value via viewmodel
    ok = vm.set_value("")
    assert ok
    # Value should be preserved and user_locked_value should remain True
    assert node.value == 5
    assert getattr(node, "user_locked_value", False) is True


def test_dialog_vm_preserves_value_on_empty_apply():
    node = DummyNode()

    # Dialog VM is abstract; instantiate a minimal concrete subclass for testing
    class ConcreteDialogVM(DialogNodeEditorViewModel):
        def initialize(self):
            pass

        def cleanup(self):
            pass

    dvm = ConcreteDialogVM()
    dvm.load_from_node(node)

    # Simulate empty string in editor and apply
    dvm.set_value("")
    assert dvm.get_value() == 5 or dvm.get_value() == ""
    dvm.apply_to_node()

    # Node value must remain unchanged
    assert node.value == 5
    assert getattr(node, "user_locked_value", False) is True


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_dialog_ok_ignores_empty_value(qapp):
    node = DummyNode()
    dlg = NodeEditorDialog(node)
    # Access underlying MVVM value widget
    val_w = dlg._dlg._widgets["value"]
    assert hasattr(val_w, "setPlainText")

    # Set the widget to empty and ensure _on_ok does not call vm.set_value
    val_w.setPlainText("")
    qapp.processEvents()

    calls = {}
    original_set_value = dlg._vm.set_value

    def _spy(val, _orig=original_set_value):
        calls["val"] = val
        return _orig(val)

    dlg._vm.set_value = _spy
    dlg._dlg._on_ok()

    assert "val" not in calls, "_on_ok should not call vm.set_value for empty input"
    assert node.value == 5
    assert getattr(node, "user_locked_value", False) is True

    dlg.close()
