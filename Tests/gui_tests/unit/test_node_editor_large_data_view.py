import pytest

try:
    from PyQt6.QtWidgets import QApplication, QTextEdit

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


class DummyNode:
    def __init__(self):
        self.name = "big"
        # large string
        self.value = "x" * 400
        # large inputs list
        self.inputs = list(range(50))


def test_large_value_and_inputs_use_textedit(qtbot):
    app = QApplication.instance() or QApplication([])
    node = DummyNode()

    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    # Value should be a QTextEdit
    assert "value" in dlg._widgets
    assert isinstance(dlg._widgets["value"], QTextEdit)
    assert dlg._widgets["value"].toPlainText() == node.value

    # Inputs should be a QTextEdit (one item per line)
    assert "inputs" in dlg._widgets
    assert isinstance(dlg._widgets["inputs"], QTextEdit)
    lines = dlg._widgets["inputs"].toPlainText().splitlines()
    assert len(lines) == len(node.inputs)
    assert lines[0] == "0"
    assert lines[-1] == str(node.inputs[-1])
