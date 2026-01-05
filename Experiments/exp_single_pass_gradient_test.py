"""
Single-pass gradient test: Verify backprop logic by comparing one forward+backward pass.

This is the most direct test of backprop correctness:
1. Set up identical weights in both Classic and ForwardProcessing
2. Run ONE forward pass + ONE backward pass on a single sample
3. Compare gradients (dW values) - they should be IDENTICAL

If gradients match, backprop logic is correct.
If gradients differ, there's a bug in BackpropGraphForwardProcessing.
"""

import random

import numpy as np

from ClassicMLP import ClassicMLP
from ComputationalGraphs.Core.BackpropGraphForwardProcessing import (
    BackpropGraphForwardProcessing,
)
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from ComputationalGraphs.Nodes.LinearNode import LinearNode
from ComputationalGraphs.Nodes.SigmoidNode import SigmoidNode

print("=" * 80)
print("SINGLE-PASS GRADIENT TEST")
print("Comparing gradients from one forward+backward pass")
print("=" * 80)

# Simple 2-2-1 architecture for easy debugging
# Single sample: [1, 0] -> [1]
X_sample = np.array([[1.0, 0.0]])
y_sample = np.array([[1.0]])

learning_rate = 0.5

# ============================================================================
# 1. Create ClassicMLP with known weights
# ============================================================================
print("\n[1] Creating ClassicMLP with fixed weights...")

# Use fixed weights for reproducibility
W_input_hidden = np.array(
    [
        [0.1, 0.2],  # input 0 -> hidden 0, hidden 1
        [0.3, 0.4],  # input 1 -> hidden 0, hidden 1
    ]
)
W_hidden_output = np.array(
    [
        [0.5],  # hidden 0 -> output 0
        [0.6],  # hidden 1 -> output 0
    ]
)

classic_mlp = ClassicMLP(
    input_size=2,
    hidden_layers=[2],
    output_size=1,
    hidden_activation="sigmoid",
    output_activation="linear",
    learning_rate=learning_rate,
    use_bias=False,
)

classic_mlp.weights[0] = W_input_hidden.copy()
classic_mlp.weights[1] = W_hidden_output.copy()

print("  Weights set:")
print(f"    W0 (input->hidden):\n{classic_mlp.weights[0]}")
print(f"    W1 (hidden->output):\n{classic_mlp.weights[1]}")

# ============================================================================
# 2. Manual forward pass in Classic
# ============================================================================
print("\n[2] Classic forward pass...")

activations = classic_mlp.forward_pass(X_sample)

print(f"  Input: {activations[0]}")
print(f"  Hidden (pre-activation z): {np.dot(activations[0], classic_mlp.weights[0])}")
print(f"  Hidden (sigmoid): {activations[1]}")
print(f"  Output (linear): {activations[2]}")

# ============================================================================
# 3. Manual backward pass in Classic - capture gradients BEFORE applying
# ============================================================================
print("\n[3] Classic backward pass (computing gradients)...")

# Output error
output_error = activations[-1] - y_sample  # (pred - true)
print(f"  Output error (pred - y): {output_error}")

# Output delta (for linear: derivative = 1)
output_delta = output_error * 1.0  # linear derivative
print(f"  Output delta: {output_delta}")

# Hidden error (backprop through output weights)
hidden_error = np.dot(output_delta, classic_mlp.weights[1].T)
print(f"  Hidden error: {hidden_error}")

# Hidden delta (sigmoid derivative: a*(1-a))
hidden_sigmoid = activations[1]
sigmoid_deriv = hidden_sigmoid * (1 - hidden_sigmoid)
hidden_delta = hidden_error * sigmoid_deriv
print(f"  Sigmoid derivative: {sigmoid_deriv}")
print(f"  Hidden delta: {hidden_delta}")

# Weight gradients (dW = activation.T @ delta)
dW_hidden_output = np.dot(activations[1].T, output_delta)
dW_input_hidden = np.dot(activations[0].T, hidden_delta)

print(f"\n  dW0 (input->hidden):\n{dW_input_hidden}")
print(f"  dW1 (hidden->output):\n{dW_hidden_output}")

# Weight update = lr * dW
print(f"\n  LR * dW0:\n{learning_rate * dW_input_hidden}")
print(f"  LR * dW1:\n{learning_rate * dW_hidden_output}")

# ============================================================================
# 4. Create ForwardProcessing MLP with same weights
# ============================================================================
print("\n[4] Creating ForwardProcessing MLP with same weights...")

mlp_forward = MLPGraphForwardProcessing(
    numInputs=2,
    numOutputs=1,
    numHiddenLayers=1,
    hiddenLayerSizes=[2],
    activationFunction=SigmoidNode,
    outputLayerType=LinearNode,
)
mlp_forward.BuildMLP()

# Set weights to match Classic
for node in mlp_forward.nodes:
    if node.name == "W_x0H0N0":
        node.value = W_input_hidden[0, 0]
    elif node.name == "W_x0H0N1":
        node.value = W_input_hidden[0, 1]
    elif node.name == "W_x1H0N0":
        node.value = W_input_hidden[1, 0]
    elif node.name == "W_x1H0N1":
        node.value = W_input_hidden[1, 1]
    elif node.name == "W_H0N0y0":
        node.value = W_hidden_output[0, 0]
    elif node.name == "W_H0N1y0":
        node.value = W_hidden_output[1, 0]

# Build backprop
backprop_forward = BackpropGraphForwardProcessing(
    mlp_forward, learningRate=learning_rate
)
backprop_forward.BuildBackprop()

# Combine graphs
fullGraph = Graph()
for node in mlp_forward.nodes:
    fullGraph.AddNode(node)
for node in backprop_forward.nodes:
    fullGraph.AddNode(node)
fullGraph.starting_nodes = mlp_forward.starting_nodes + [backprop_forward.lrNode]
fullGraph.UpdateAdjacencyMatrix()

# Load single sample - ForwardProcessing expects row-per-sample format
mlp_forward.LoadData([[1.0, 0.0]], [[1.0]])  # [sample] where sample is [features...]

processor = GraphProcessor(fullGraph, verbose=False)
mlp_forward.PrepareForForwardProcessing(processor)

print("  ForwardProcessing graph built and prepared")

# Verify weights match
print("\n  Verifying initial weights match Classic:")
for node in mlp_forward.nodes:
    if node.name.startswith("W_"):
        print(f"    {node.name}: {node.value}")

# ============================================================================
# 5. Run ForwardProcessing for one complete pass
# ============================================================================
print("\n[5] Running ForwardProcessing graph...")

# Get pass length
pass_length = mlp_forward.GetPassLength()
print(f"  Pass length (estimated): {pass_length} iterations")

# Actually trace which nodes are processed each iteration
print("\n  Tracing active nodes per iteration:")
for i in range(30):
    active_before = [n.name for n in fullGraph.nodes if getattr(n, "processed", False)]
    processor.ForwardProcessing(iterations=1)
    active_after = [n.name for n in fullGraph.nodes if getattr(n, "processed", False)]
    newly_processed = set(active_after) - set(active_before)

    # Find key backprop nodes
    key_nodes = [
        n for n in newly_processed if any(p in n for p in ["EG_", "LRMult_", "dW_"])
    ]
    if key_nodes:
        print(f"    Iter {i}: {key_nodes}")

    # Check when dW gets a value
    for node in fullGraph.nodes:
        if node.name == "dW_H0N0y0" and node.value != 0.0:
            print(f"    Iter {i}: dW_H0N0y0 = {node.value}")
            break

print(f"\n  Completed 30 iterations")

# ============================================================================
# 6. Extract values from ForwardProcessing graph
# ============================================================================
print("\n[6] ForwardProcessing node values after one pass:")

# Find key nodes
for node in fullGraph.nodes:
    if node.name in ["x0", "x1"]:
        print(f"  Input {node.name}: {node.value}")

# Hidden activations
for node in fullGraph.nodes:
    if node.name.startswith("Act_L0N"):
        print(f"  Hidden {node.name}: {node.value}")

# Output
for node in fullGraph.nodes:
    if node.name == "y0":
        print(f"  Output {node.name}: {node.value}")

# Error
for node in fullGraph.nodes:
    if node.name.startswith("Error_y"):
        print(f"  Error {node.name}: {node.value}")

# Error gradients
print("\n  Error gradients:")
for node in fullGraph.nodes:
    if node.name.startswith("EG_"):
        print(f"    {node.name}: {node.value}")

# LR multiplications
print("\n  LR * gradients:")
for node in fullGraph.nodes:
    if node.name.startswith("LRMult_"):
        print(f"    {node.name}: {node.value}")

# dW nodes
print("\n  dW nodes (lr * gradient * activation):")
for node in fullGraph.nodes:
    if node.name.startswith("dW_"):
        print(f"    {node.name}: {node.value}")

# ============================================================================
# 7. Compare gradients
# ============================================================================
print("\n" + "=" * 80)
print("GRADIENT COMPARISON")
print("=" * 80)

# Get dW values from graph
graph_dW = {}
for node in fullGraph.nodes:
    if node.name.startswith("dW_"):
        graph_dW[node.name] = node.value

# Classic dW values (lr * dW)
classic_dW = {
    "dW_x0H0N0": learning_rate * dW_input_hidden[0, 0],
    "dW_x0H0N1": learning_rate * dW_input_hidden[0, 1],
    "dW_x1H0N0": learning_rate * dW_input_hidden[1, 0],
    "dW_x1H0N1": learning_rate * dW_input_hidden[1, 1],
    "dW_H0N0y0": learning_rate * dW_hidden_output[0, 0],
    "dW_H0N1y0": learning_rate * dW_hidden_output[1, 0],
}

print("\nExpected (Classic) vs Actual (Graph):")
all_match = True
for name in sorted(classic_dW.keys()):
    expected = classic_dW[name]
    actual = graph_dW.get(name, "NOT FOUND")
    if isinstance(actual, float):
        diff = abs(expected - actual)
        match = diff < 1e-6
        status = "✓" if match else "✗"
        if not match:
            all_match = False
        print(
            f"  {name}: Classic={expected:.6f}, Graph={actual:.6f}, Diff={diff:.6f} {status}"
        )
    else:
        all_match = False
        print(f"  {name}: Classic={expected:.6f}, Graph={actual} ✗")

print("\n" + "=" * 80)
if all_match:
    print("✓ ALL GRADIENTS MATCH - Backprop logic is CORRECT")
else:
    print("✗ GRADIENTS DIFFER - There's a bug in BackpropGraphForwardProcessing")
print("=" * 80)
