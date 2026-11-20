"""Compare a scalar-node concurrent XOR MLP with a NumPy MLP.

Run from the repository root after installing the reference package:
    python benchmarks/benchmark_xor.py --iterations 5000
"""

import argparse
import json
import platform
import random
import time

import numpy as np

from zorvan_reference.Core.BackpropGraph import BackpropGraph
from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Core.GraphProcessor import GraphProcessor
from zorvan_reference.Core.MLPGraph import MLPGraph
from zorvan_reference.Nodes.LinearNode import LinearNode
from zorvan_reference.Nodes.SigmoidNode import SigmoidNode


X = np.asarray([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
Y = np.asarray([[0.0], [1.0], [1.0], [0.0]])


def build_reference(learning_rate):
    random.seed(42)
    mlp = MLPGraph(
        numInputs=2,
        numOutputs=1,
        numHiddenLayers=1,
        hiddenLayerSizes=[4],
        activationFunction=SigmoidNode,
        outputLayerType=LinearNode,
        use_bias=True,
    )
    mlp.BuildMLP()
    mlp.LoadData(X.T.tolist(), Y.T.tolist())
    backprop = BackpropGraph(mlp, learningRate=learning_rate)
    backprop.BuildBackprop()

    combined = Graph()
    for node in mlp.nodes + backprop.nodes:
        combined.AddNode(node)

    weights = [
        np.asarray([[node.value for node in row] for row in layer], dtype=float)
        for layer in mlp.weightLayers
    ]
    biases = [
        np.asarray([node.value for node in layer], dtype=float)
        for layer in mlp.biasLayers
    ]
    return GraphProcessor(combined, max_workers=1, verbose=False), weights, biases


def run_numpy(weights, biases, learning_rate, iterations):
    w1, w2 = (value.copy() for value in weights)
    b1, b2 = (value.copy() for value in biases)
    for tick in range(iterations):
        sample = tick % len(X)
        hidden = 1.0 / (1.0 + np.exp(-(X[sample] @ w1 + b1)))
        output = hidden @ w2 + b2
        delta_output = output - Y[sample]
        delta_hidden = (delta_output @ w2.T) * hidden * (1.0 - hidden)
        w2 -= learning_rate * np.outer(hidden, delta_output)
        b2 -= learning_rate * delta_output
        w1 -= learning_rate * np.outer(X[sample], delta_hidden)
        b1 -= learning_rate * delta_hidden


def benchmark(iterations):
    learning_rate = 0.1
    processor, weights, biases = build_reference(learning_rate)

    start = time.perf_counter()
    processor.ComputeGraph(iterations=iterations)
    reference_seconds = time.perf_counter() - start

    start = time.perf_counter()
    run_numpy(weights, biases, learning_rate, iterations)
    numpy_seconds = time.perf_counter() - start

    return {
        "iterations": iterations,
        "architecture": [2, 4, 1],
        "examples_per_iteration": 1,
        "reference_seconds": reference_seconds,
        "numpy_seconds": numpy_seconds,
        "reference_over_numpy": reference_seconds / numpy_seconds,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor_nodes": len(processor.graph.nodes),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--output", help="optional JSON result path")
    args = parser.parse_args()
    result = benchmark(args.iterations)
    encoded = json.dumps(result, indent=2)
    print(encoded)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(encoded + "\n")


if __name__ == "__main__":
    main()
