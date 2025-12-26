import pytest

try:
    from PyQt6.QtWidgets import QApplication, QSpinBox

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


def test_spinbox_updates_do_not_crash_on_rapid_changes(qtbot):
    app = QApplication.instance() or QApplication([])
    node = DataStreamNode(name="ds", data=[1, 2, 3], initialDelay=0)

    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    assert "initialDelay" in dlg._widgets
    spin = dlg._widgets["initialDelay"]
    assert isinstance(spin, QSpinBox)

    # Rapidly change the value multiple times to simulate quick wheel scrolls
    for i in range(5):
        spin.stepBy(1)
    # Allow scheduled singleShot callbacks to run
    qtbot.wait(50)

    # Dialog should still exist and the node property should be updated
    assert dlg is not None
    assert isinstance(node.initialDelay, int)
    assert node.initialDelay == spin.value()
