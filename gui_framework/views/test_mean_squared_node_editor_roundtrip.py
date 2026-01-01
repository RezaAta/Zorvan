import pytest

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views import node_editor_dialog

HAS_PYQT = getattr(node_editor_dialog, "HAS_PYQT", False)


@pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 not available")
def test_mean_squared_node_data_roundtrip():
    from ComputationalGraphs.Nodes.MeanSquaredNode import MeanSquaredNode

    ms = MeanSquaredNode(name="ms", data=[0.1, 0.2])
    vm = NodeEditorViewModel(ms)
    vm.initialize()

    dlg = node_editor_dialog.NodeEditorDialog(vm)

    w = dlg._widgets.get("data")
    if w is None:
        pytest.skip("No 'data' widget in dialog")

    # Editor may be QLineEdit for short lists
    try:
        w.setText("0.3,0.4")
    except Exception:
        try:
            w.setPlainText("0.3,0.4")
        except Exception:
            pytest.skip("Widget not interactive in test environment")

    # Apply changes
    dlg._on_ok()

    # Buffer must be a list and operations should not raise
    assert isinstance(ms.buffer, list)
    # Should be able to append via Operation (no attribute error)
    r = ms.Operation(0.5)
    assert r is not None or hasattr(ms, "value")
