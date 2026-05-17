import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


class SmallNode:
    def __init__(self):
        self.name = "small"
        self.value = "short"


class LargeNode:
    def __init__(self):
        self.name = "large"
        self.value = "\n".join([str(i) for i in range(200)])


def test_textedit_resizes_for_content(qtbot):
    app = QApplication.instance() or QApplication([])

    small = SmallNode()
    vm = NodeEditorViewModel(small)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    val_w = dlg._widgets["value"]
    small_h = val_w.height()

    large = LargeNode()
    vm.load_node(large)
    # Trigger properties changed
    dlg._on_properties_changed(None, None)

    val_w_large = dlg._widgets["value"]
    large_h = val_w_large.height()

    assert large_h > small_h
    # Heights respect configured limits
    assert small_h >= 50
    assert large_h <= 300
