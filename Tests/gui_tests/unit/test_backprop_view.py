import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for dialog view tests")

from gui_framework.viewmodels.dialogs.backprop_viewmodel import BackpropViewModel
from gui_framework.views.dialogs.backprop_dialog import BackpropDialog
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.SigmoidNode import SigmoidNode


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_backprop_dialog_add(qapp):
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[2],
        activationFunction=SigmoidNode,
    )
    mlp.BuildMLP()

    vm = BackpropViewModel(mlp)
    vm.initialize()

    dlg = BackpropDialog(vm)
    # Ensure widgets exist
    assert hasattr(dlg, "lr_spin")
    assert hasattr(dlg, "add_btn")

    # Set a learning rate and trigger add
    dlg.lr_spin.setValue(0.2)
    dlg._on_add()

    g = dlg.get_graph()
    assert g is not None
    assert len(g.nodes) > 0
    dlg.close()
