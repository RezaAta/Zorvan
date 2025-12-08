from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Nodes.InitializableContainerNode import (
    InitializableContainerNode,
)


def test_mlp_weights_are_initializable():
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, hiddenLayerSizes=[2])
    mlp.BuildMLP()
    # Check first layer weights
    for row in mlp.weightLayers[0]:
        for weight_node in row:
            assert isinstance(weight_node, InitializableContainerNode)

    # Check last layer weights
    for row in mlp.weightLayers[-1]:
        for weight_node in row:
            assert isinstance(weight_node, InitializableContainerNode)
