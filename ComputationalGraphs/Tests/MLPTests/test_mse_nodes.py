import pytest

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode


def test_mse_nodes_concurrent():
    # Build small concurrent MLP for XOR
    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load XOR data (row-per-feature)
    X = [[0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 1.0]]
    y = [[0.0, 1.0, 1.0, 0.0]]
    mlp.LoadData(X, y)

    # Create error buffers and ensure MSE nodes added
    iterations = 10
    mlp.CreateErrorBuffers(iterations)
    assert hasattr(mlp, "mseNodes")
    assert len(mlp.mseNodes) == mlp.numOutputs
    # dataset size = len(X[0]) = 4
    for mse_node in mlp.mseNodes:
        assert mse_node.bufferSize == len(X[0])
        assert mse_node.mode == "continuous"
        # Check predecessor is error node
        assert len(mse_node.predecessors) == 1
        assert mse_node.predecessors[0].name.startswith("Error_y")


def test_mse_nodes_forward():
    # Build forward-processing MLP for XOR
    mlp = MLPGraphForwardProcessing(numInputs=2, numOutputs=1, numHiddenLayers=1, activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load XOR data (row-per-sample)
    X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    y = [[0.0], [1.0], [1.0], [0.0]]
    mlp.LoadData(X, y)

    iterations = 10
    mlp.CreateErrorBuffers(iterations, allowNone=True)
    assert hasattr(mlp, "mseNodes")
    assert len(mlp.mseNodes) == mlp.numOutputs
    # dataset size = len(X) = 4
    for mse_node in mlp.mseNodes:
        assert mse_node.bufferSize == len(X)
        assert mse_node.mode == "continuous"
        # Check predecessor is error node
        assert len(mse_node.predecessors) == 1
        assert mse_node.predecessors[0].name.startswith("Error_y")
