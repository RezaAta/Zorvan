import pytest

from zorvan_reference.Core.MLPGraph import MLPGraph
from zorvan_reference.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from zorvan_reference.Nodes.InitializableContainerNode import InitializableContainerNode


@pytest.mark.parametrize(
    "mlp_class",
    [MLPGraph, MLPGraphForwardProcessing],
)
def test_mlp_weights_are_initializable(mlp_class):
    mlp = mlp_class(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[2],
    )
    mlp.BuildMLP()

    for row in mlp.weightLayers[0]:
        for weight_node in row:
            assert isinstance(weight_node, InitializableContainerNode)

    for row in mlp.weightLayers[-1]:
        for weight_node in row:
            assert isinstance(weight_node, InitializableContainerNode)
