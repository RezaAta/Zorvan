"""
MLP piecewise function example (Concurrent)

Builds a concurrent MLP with 1 input, 1 hidden layer of 3 Sigmoid neurons
and 1 linear output. Loads a synthetic piecewise dataset and runs concurrent
training via GraphProcessor.

This is a convenience script for CLI testing and reproduces behavior used
for the GUI example in `examples_loader.py`.
"""

import numpy as np

from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Core.Graph import Graph


def piecewise_function(x):
    # f(x) = sin(x) for x < 0
    # f(x) = 0 for 0 <= x < 1
    # f(x) = 2x + 1 for x >= 1
    return np.where(x < 0, np.sin(x), np.where(x < 1, 0.0, 2.0 * x + 1.0))


def build_and_train(iterations=1000, verbose=True):
    # Build dataset
    x_vals = np.linspace(-3.0, 4.0, 300)
    y_vals = piecewise_function(x_vals)

    # Convert to row-per-feature (features, samples) for concurrent MLPGraph
    X = [x_vals.tolist()]
    y = [y_vals.tolist()]

    # Build concurrent MLP: 1 input -> 3 hidden neurons -> 1 linear output
    mlp = MLPGraph(numInputs=1, numOutputs=1, numHiddenLayers=1, hiddenLayerSizes=[3], activationFunction=SigmoidNode, outputLayerType=LinearNode)
    mlp.BuildMLP()

    # Load data
    mlp.LoadData(X, y)

    # Create backprop graph
    backprop = BackpropGraph(mlp, learningRate=0.01)
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

    # Retrieve predictions from mlp.predictionBuffers if they exist, else read output activation
    try:
        preds = [p.value for p in mlp.predictionBuffers]
    except Exception:
        # Fallback: run one last pass and get output node values (may be batch-based)
        preds = []
        for outAdd, outAct in mlp.outputLayer:
            preds.append(outAct.value)

    # Compute MSE over the final values collected from output
    # This is a simple diagnostic - it's not representative for full training history
    final_output = None
    try:
        final_output = mlp.predictionBuffers[0].buffer.copy()
    except Exception:
        try:
            final_output = [out[1].value for out in mlp.outputLayer]
        except Exception:
            final_output = None

    if final_output is not None:
        print("Sample predicted output values (recent buffer or final values):")
        if isinstance(final_output, (list, tuple)):
            print(final_output[:10])
        else:
            print(final_output)

    print("Training completed.")


if __name__ == '__main__':
    build_and_train(iterations=500, verbose=True)
