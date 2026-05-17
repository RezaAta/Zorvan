"""
Test concurrent MLP with bias on XOR problem.
"""

import random

import numpy as np

from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.SigmoidNode import SigmoidNode

# XOR dataset
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])
X_concurrent = X.T.tolist()  # Shape: (features, samples)
y_concurrent = y.T.tolist()

print("=" * 80)
print("CONCURRENT MLP WITH BIAS TEST ON XOR")
print("=" * 80)

# Test 1: With bias
print("\n--- WITH BIAS ---")
random.seed(42)
mlp_bias = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=[4],
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
    use_bias=True,
)
mlp_bias.BuildMLP()
mlp_bias.LoadData(X_concurrent, y_concurrent)

backprop_bias = BackpropGraph(mlp_bias, learningRate=0.1)
backprop_bias.BuildBackprop()

# Combine graphs
graph_bias = Graph()
for node in mlp_bias.nodes:
    graph_bias.AddNode(node)
for node in backprop_bias.nodes:
    graph_bias.AddNode(node)

processor_bias = GraphProcessor(graph_bias)

# Store initial values
init_biases = {b.name: b.value for layer in mlp_bias.biasLayers for b in layer}
init_weights = {}
for layer in mlp_bias.weightLayers:
    for row in layer:
        for w in row:
            init_weights[w.name] = w.value

# Train
iterations = 5000
print(f"Training for {iterations} iterations...")
processor_bias.ComputeGraph(iterations=iterations)

# Check final values
print("\nBias changes:")
bias_changed = 0
for layer in mlp_bias.biasLayers:
    for b in layer:
        diff = abs(b.value - init_biases[b.name])
        if diff > 1e-6:
            bias_changed += 1
        print(f"  {b.name}: {init_biases[b.name]:.4f} -> {b.value:.4f}")
print(f"Biases changed: {bias_changed}/{len(init_biases)}")

print("\nWeight changes (sample):")
weight_changed = 0
count = 0
for layer in mlp_bias.weightLayers:
    for row in layer:
        for w in row:
            diff = abs(w.value - init_weights[w.name])
            if diff > 1e-6:
                weight_changed += 1
            if count < 4:
                print(f"  {w.name}: {init_weights[w.name]:.4f} -> {w.value:.4f}")
            count += 1
print(f"Weights changed: {weight_changed}/{len(init_weights)}")

print("\nFinal error:")
for e in mlp_bias.errorLayer:
    print(f"  {e.name}: {e.value:.6f}")

# Test 2: Without bias (comparison)
print("\n--- WITHOUT BIAS ---")
random.seed(42)
mlp_nobias = MLPGraph(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=[4],
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
    use_bias=False,
)
mlp_nobias.BuildMLP()
mlp_nobias.LoadData(X_concurrent, y_concurrent)

backprop_nobias = BackpropGraph(mlp_nobias, learningRate=0.1)
backprop_nobias.BuildBackprop()

graph_nobias = Graph()
for node in mlp_nobias.nodes:
    graph_nobias.AddNode(node)
for node in backprop_nobias.nodes:
    graph_nobias.AddNode(node)

processor_nobias = GraphProcessor(graph_nobias)
processor_nobias.ComputeGraph(iterations=iterations)

print("\nFinal error:")
for e in mlp_nobias.errorLayer:
    print(f"  {e.name}: {e.value:.6f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
if bias_changed > 0 and weight_changed > 0:
    print("✓ SUCCESS: Both biases and weights are training!")
else:
    print("✗ ISSUE: Some parameters not changing")
