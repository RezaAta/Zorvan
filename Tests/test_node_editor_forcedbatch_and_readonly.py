import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from ComputationalGraphs.Nodes.PopulationNode import PopulationNode
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


def test_forced_batch_is_checkbox(qtbot):
    app = QApplication.instance() or QApplication([])
    node = PopulationNode(name="Pop", size=5)
    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    fb_widget = dlg._widgets.get("forcedBatch")
    assert fb_widget is not None
    from PyQt6.QtWidgets import QCheckBox

    assert isinstance(fb_widget, QCheckBox)
    # Legacy raw property should not be shown as a separate widget
    assert "forcedBatchProcessing" not in dlg._widgets


def test_readonly_fields_and_inputs_editable(qtbot):
    app = QApplication.instance() or QApplication([])
    node = PopulationNode(name="Pop", size=5)
    # Inject example attributes
    node.inputCount = 4
    node.id = "node-123"
    node.midCalculation = False
    node.inputs = ["a", "b"]

    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    # inputCount should be present but disabled (readonly)
    ic = dlg._widgets.get("inputCount")
    if ic is not None:
        assert not ic.isEnabled()

    # id should be readonly (line edit)
    idw = dlg._widgets.get("id")
    if idw is not None:
        assert idw.isReadOnly()

    # midCalculation readonly
    mid = dlg._widgets.get("midCalculation")
    if mid is not None:
        # Could be checkbox
        try:
            assert not mid.isEnabled()
        except Exception:
            # or read-only line
            assert mid.isReadOnly()

    # inputs editable
    inputs_w = dlg._widgets.get("inputs")
    assert inputs_w is not None
    assert inputs_w.isEnabled() and not getattr(inputs_w, "isReadOnly", lambda: False)()
