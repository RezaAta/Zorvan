import numpy as np

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def test_prepare_for_test_preserves_biases():
    # Small synthetic dataset (row-per-feature format expected by MLPGraph)
    X = [[0.1, 0.2, 0.3], [0.2, 0.1, 0.2]]  # 2 features, 3 samples
    y = [[1, 0, 1]]

    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[3],
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
        add_bias=True,
    )
    mlp.BuildMLP()

    # Assign distinct bias values for detection
    for i, layer in enumerate(mlp.biasLayers):
        for j, b in enumerate(layer):
            b.value = float((i + 1) * (j + 1) * 1.2345)

    # Build backprop so bias nodes get dB predecessors
    back = BackpropGraph(mlp, learningRate=0.01)
    back.BuildBackprop()

    # Ensure nodes present in a combined graph for training if needed
    g = Graph()
    for n in mlp.nodes:
        g.AddNode(n)
    for n in back.nodes:
        g.AddNode(n)

    # Load data and warmup
    mlp.LoadData(X, y)
    proc = GraphProcessor(g, max_workers=1, verbose=False)
    proc.ComputeGraphSingleThread(3 * (mlp.numHiddenLayers + 1))

    # Record bias values before PrepareForTest
    before = [[float(b.value) for b in layer] for layer in mlp.biasLayers]

    # Prepare for test and run a short forward pass
    mlp.PrepareForTest(X, y)
    test_proc = GraphProcessor(mlp, max_workers=1, verbose=False)
    test_proc.ComputeGraphSingleThread(len(X[0]) + 3 * (mlp.numHiddenLayers + 1))

    after = [[float(b.value) for b in layer] for layer in mlp.biasLayers]

    # Biases should not be reset to zero and should remain close to pre-test values
    for b_before, b_after in zip(before, after):
        assert np.allclose(b_before, b_after, rtol=1e-2, atol=1e-2)
