"""
MLP piecewise function example (Concurrent)

Builds a concurrent MLP with 1 input, 1 hidden layer of 3 Sigmoid neurons
and 1 linear output. Loads a synthetic piecewise dataset and runs concurrent
training via GraphProcessor.

This is a convenience script for CLI testing and reproduces behavior used
for the GUI example in `examples_loader.py`.

The example now uses x in [-3, 3] with equal samples per region and the
piecewise function:
    f(x) = x^2 if x <= -1
    f(x) = 0   if -1 < x < 1
    f(x) = 2x if x >= 1
"""

import numpy as np

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def piecewise_function(x):
    # New piecewise function (Option B):
    # f(x) = x^2 for x <= -1
    # f(x) = 0 for -1 < x < 1
    # f(x) = 2x for x >= 1
    return np.where(x <= -1.0, x**2, np.where(x < 1.0, 0.0, 2.0 * x))


def build_and_train(iterations=1000, verbose=True):
    # Build dataset (x in [-3,3] with equal samples across three regions)
    n_total = 300
    n_regions = 3
    base = n_total // n_regions
    extra = n_total % n_regions
    counts = [base + (1 if i < extra else 0) for i in range(n_regions)]
    x1 = np.linspace(-3.0, -1.0, counts[0], endpoint=True)
    x2 = np.linspace(-1.0, 1.0, counts[1] + 1, endpoint=False)[1:]
    x3 = np.linspace(1.0, 3.0, counts[2], endpoint=True)
    x_vals = np.concatenate([x1, x2, x3])
    y_vals = piecewise_function(x_vals)

    # Convert to row-per-feature (features, samples) for concurrent MLPGraph
    X = [x_vals.tolist()]
    y = [y_vals.tolist()]

    # Build concurrent MLP: 1 input -> 3 hidden neurons -> 1 linear output
    mlp = MLPGraph(
        numInputs=1,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[3],
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
    )
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

    fullGraph.starting_nodes = [
        input_pair[0] for input_pair in mlp.inputLayer
    ] + mlp.labelLayer
    fullGraph.UpdateAdjacencyMatrix()

    # Setup processor and run training
    processor = GraphProcessor(fullGraph, verbose=verbose, auto_threading=False)

    # Warmup iterations to fill buffers (if needed)
    try:
        buffer_nodes = [n for n in mlp.nodes if isinstance(n, BufferNode)]
        if buffer_nodes:
            warmup = max(getattr(b, "bufferSize", 1) for b in buffer_nodes) + 2
        else:
            warmup = 10
    except Exception:
        warmup = 10
    processor.ComputeGraph(
        iterations=warmup,
        exec_options=GraphProcessor.ExecutionOptions(step_interval_ms=0),
    )

    # Main training iterations
    processor.ComputeGraph(
        iterations=iterations,
        exec_options=GraphProcessor.ExecutionOptions(step_interval_ms=0),
    )

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


if __name__ == "__main__":
    build_and_train(iterations=500, verbose=True)
