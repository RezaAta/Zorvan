import pytest

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from gui_framework.viewmodels.dialogs.backprop_viewmodel import BackpropViewModel


def test_backprop_viewmodel_add_remove():
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
    assert vm.get_learning_rate() == 0.01

    vm.set_learning_rate(0.5)
    assert vm.get_learning_rate() == 0.5

    ok = vm.add_backprop()
    assert ok
    g = vm.get_generated_graph()
    assert g is not None
    # Generated graph should contain nodes
    assert len(g.nodes) > 0

    # Remove backprop: should succeed (idempotent) or return True
    ok2 = vm.remove_backprop()
    assert ok2
    g2 = vm.get_generated_graph()
    assert g2 is not None
