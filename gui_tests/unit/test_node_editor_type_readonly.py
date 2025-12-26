import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from ComputationalGraphs.Nodes.InitializableContainerNode import (
    InitializableContainerNode,
)
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


def test_node_editor_shows_type_readonly(qtbot):
    app = QApplication.instance() or QApplication([])
    node = InitializableContainerNode(name="W_test", value=0.5)
    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    # The dialog should include a widget named 'type' in _widgets and it should be a label
    assert "type" in dlg._widgets
    w = dlg._widgets["type"]
    from PyQt6.QtWidgets import QLabel

    assert isinstance(w, QLabel)
    # And the displayed text should match the class name
    assert w.text() == type(node).__name__
