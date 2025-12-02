"""
MLP piecewise 2 example (Concurrent)

Builds a concurrent MLP with 1 input, 2 hidden layers (3 ReLU, 8 ReLU)
and 1 linear output. Loads a synthetic piecewise dataset and runs concurrent
training via GraphProcessor.
"""

import numpy as np

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.ReLUNode import ReLUNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Core.Graph import Graph


def piecewise_function(x):
    # f(x) = x^2 for x < 0
    # f(x) = 0 for 0 <= x <= 1
    # f(x) = 2x + 1 for x > 1
    return np.where(x < 0, x**2, np.where(x <= 1, 0.0, 2.0 * x + 1.0))


def build_and_train(iterations=1000, verbose=True):
    # Build dataset
    x_vals = np.linspace(-3.0, 4.0, 300)
    y_vals = piecewise_function(x_vals)

    # Convert to row-per-feature (features, samples) for concurrent MLPGraph
    X = [x_vals.tolist()]
    y = [y_vals.tolist()]

    # Build concurrent MLP: 1 input -> [3 ReLU] -> [8 ReLU] -> 1 linear output
    mlp = MLPGraph(numInputs=1, numOutputs=1, numHiddenLayers=2, hiddenLayerSizes=[3, 8], activationFunction=ReLUNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load data
    mlp.LoadData(X, y)

    # Create backprop graph
    backprop = BackpropGraph(mlp, learningRate=0.001)
    backprop.BuildBackprop()

    # Combine graphs
    fullGraph = Graph()
    for node in mlp.nodes:
        fullGraph.AddNode(node)
    for node in backprop.nodes:
        fullGraph.AddNode(node)

    fullGraph.starting_nodes = [input_pair[0] for input_pair in mlp.inputLayer] + mlp.labelLayer
    fullGraph.UpdateAdjacencyMatrix()

    # Setup processor and run training
    processor = GraphProcessor(fullGraph, verbose=verbose, auto_threading=False)

    # Warmup iterations to fill buffers (if needed)
    try:
        buffer_nodes = [n for n in mlp.nodes if isinstance(n, BufferNode)]
        if buffer_nodes:
            warmup = max(getattr(b, 'bufferSize', 1) for b in buffer_nodes) + 2
        else:
            warmup = 10
    except Exception:
        warmup = 10

    processor.ComputeGraph(iterations=warmup, exec_options=GraphProcessor.ExecutionOptions(step_interval_ms=0))

    # Main training iterations
    processor.ComputeGraph(iterations=iterations, exec_options=GraphProcessor.ExecutionOptions(step_interval_ms=0))

    print('Training completed.')


if __name__ == '__main__':
    build_and_train(iterations=600, verbose=True)
