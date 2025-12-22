import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for adapter test")

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.GUI.backprop_dialog import BackpropDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_backprop_adapter_constructs_and_generates(qapp):
    from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[2],
        activationFunction=SigmoidNode,
    )
    mlp.BuildMLP()

    dlg = BackpropDialog(mlp)
    # call underlying VM add directly to avoid blocking exec() behavior in tests
    try:
        res = dlg._vm.add_backprop()
    except Exception:
        res = False
    assert res is True
    g = dlg.get_graph()
    assert g is not None
    assert len(g.nodes) > 0
    dlg.close()
